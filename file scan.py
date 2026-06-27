import os
import zipfile
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import imagehash
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import traceback
from datetime import datetime

# --- [ 전역 변수 ] ---
selected_folders = []
LOG_FILE_NAME = "duplicate_finder_debug.log"

# --- [ 🎨 완벽하게 보정된 테마 색상 데이터 ] ---
THEMES = {
    "✨ 모던 화이트": {
        "root_bg": "#fbfbfb", "frame_bg": "#ffffff", "text_color": "#2c3e50",
        "btn_scan": "#0066cc", "btn_scan_fg": "white",
        "btn_normal": "#f5f5f5", "btn_normal_fg": "#333333",
        "preview_bg": "#f0f2f5", "preview_fg": "#777777",
        "tree_bg": "#ffffff", "tree_fg": "#000000", "tree_field": "#ffffff"
    },
    "🌙 다크 모드": {
        "root_bg": "#1e1e1e", "frame_bg": "#252526", "text_color": "#ffffff",
        "btn_scan": "#2e7d32", "btn_scan_fg": "white",
        "btn_normal": "#3c3c3c", "btn_normal_fg": "#eeeeee",
        "preview_bg": "#2d2d30", "preview_fg": "#aaaaaa",
        "tree_bg": "#2d2d30", "tree_fg": "#ffffff", "tree_field": "#2d2d30"
    },
    "🌿 에메랄드 그린": {
        "root_bg": "#f4f7f5", "frame_bg": "#ffffff", "text_color": "#113f27",
        "btn_scan": "#117a45", "btn_scan_fg": "white",
        "btn_normal": "#eaf2ec", "btn_normal_fg": "#113f27",
        "preview_bg": "#eef5f1", "preview_fg": "#608070",
        "tree_bg": "#ffffff", "tree_fg": "#113f27", "tree_field": "#ffffff"
    }
}

# --- [ 배포 유지보수용 에러 기록 시스템 ] ---
def write_log_and_show_error(error_title, error_message, traceback_text):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE_NAME, "a", encoding="utf-8") as log_file:
            log_file.write(f"==================================================\n")
            log_file.write(f"⏰ 발생 시간: {now}\n")
            log_file.write(f"❌ 에러 타이틀: {error_title}\n")
            log_file.write(f"💬 원인 메시지: {error_message}\n")
            log_file.write(f"🛠️ 상세 추적 로그:\n{traceback_text}\n")
            log_file.write(f"==================================================\n\n")
    except Exception as log_err:
        print(f"로그 파일 작성 실패: {log_err}")

    debug_win = tk.Toplevel(root)
    debug_win.title("🛠️ 시스템 디버그 알림 (Error Report)")
    debug_win.geometry("600x480")
    debug_win.configure(bg="#f5f5f5")
    
    lbl_title = tk.Label(debug_win, text=f"⚠️ {error_title}", font=("맑은 고딕", 11, "bold"), fg="#d32f2f", bg="#f5f5f5", anchor="w")
    lbl_title.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    notice_text = f"원인: {error_message}\n\n💡 오류 복구를 위해 프로그램 폴더에 생성된\n[{LOG_FILE_NAME}] 파일을 개발자에게 전송해 주세요."
    lbl_desc = tk.Label(debug_win, text=notice_text, font=("맑은 고딕", 9, "bold"), fg="#333333", bg="#f5f5f5", justify="left", anchor="w")
    lbl_desc.pack(fill=tk.X, padx=15, pady=(0, 10))
    
    log_box = tk.Text(debug_win, font=("Consolas", 9), bg="#2d2d2d", fg="#f1f1f1", bd=0, padx=10, pady=10)
    log_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    log_box.insert(tk.END, traceback_text)
    log_box.config(state="disabled")
    
    close_btn = tk.Button(debug_win, text="확인 및 로그 창 닫기", command=debug_win.destroy, font=("맑은 고딕", 9, "bold"), bg="#e0e0e0", relief=tk.SOLID, bd=1, cursor="hand2")
    close_btn.pack(fill=tk.X, padx=15, pady=15, ipady=4)

# --- [ 기능 1: 싱글 파일 분석 ] ---
def analyze_single_file(file_info):
    full_path, file = file_info
    results = []

    if file.lower().endswith('.zip'):
        try:
            with zipfile.ZipFile(full_path, 'r') as z:
                for member in z.namelist():
                    if not member.endswith('/'):
                        try:
                            with z.open(member) as f:
                                img = Image.open(BytesIO(f.read()))
                                phash = imagehash.phash(img)
                                virtual_path = f"{full_path} ➔ [ZIP] {member}"
                                results.append((virtual_path, phash))
                        except:
                            pass
        except:
            pass
    else:
        try:
            with open(full_path, 'rb') as f:
                img = Image.open(f)
                phash = imagehash.phash(img)
                results.append((full_path, phash))
        except:
            pass
            
    return results

# --- [ 기능 2: 폴더 설정 ] ---
def add_folder():
    folder = filedialog.askdirectory()
    if folder and folder not in selected_folders:
        selected_folders.append(folder)
        refresh_folder_list()

def remove_folder():
    try:
        selected_idx = folder_listbox.curselection()[0]
        selected_folders.pop(selected_idx)
        refresh_folder_list()
    except IndexError:
        messagebox.showwarning("알림", "삭제할 폴더를 목록에서 먼저 선택해 주세요.")

def refresh_folder_list():
    folder_listbox.delete(0, tk.END)
    for folder in selected_folders:
        folder_listbox.insert(tk.END, folder)

# --- [ 기능 3: 고속 검색 엔진 ] ---
def start_scan():
    try:
        if not selected_folders:
            messagebox.showerror("에러", "검사할 폴더를 최소 하나 이상 추가해 주세요.")
            return

        result_tree.delete(*result_tree.get_children())
        status_label.config(text="🔎 파일 목록 수집 중...")
        progress_bar['value'] = 0
        preview_label.config(image='', text="🖼️ 여기에 미리보기가 표시됩니다.")
        root.update()

        all_files = []
        for folder in selected_folders:
            for root_dir, dirs, files in os.walk(folder):
                for file in files:
                    all_files.append((os.path.join(root_dir, file), file))

        total_files = len(all_files)
        if total_files == 0:
            messagebox.showinfo("안내", "검사할 파일이 없습니다.")
            status_label.config(text="대기 중")
            return

        image_hashes = {}
        status_label.config(text=f"⏳ 분석 중 (0/{total_files})...")
        root.update()

        processed_count = 0
        with ThreadPoolExecutor(max_workers=None) as executor:
            futures = executor.map(analyze_single_file, all_files)
            for file_results in futures:
                processed_count += 1
                if processed_count % 10 == 0 or processed_count == total_files:
                    progress = int((processed_count / total_files) * 100)
                    progress_bar['value'] = progress
                    status_label.config(text=f"⏳ 분석 중... ({processed_count}/{total_files})")
                    root.update()
                    
                for virtual_path, phash in file_results:
                    if phash:
                        image_hashes[virtual_path] = phash

        status_label.config(text="📊 유사도 최종 대조 중...")
        root.update()

        paths = list(image_hashes.keys())
        group_id = 1
        has_duplicates = False

        for i in range(len(paths)):
            current_duplicates = []
            path1 = paths[i]
            hash1 = image_hashes[path1]
            if hash1 is None: continue

            for j in range(i + 1, len(paths)):
                path2 = paths[j]
                hash2 = image_hashes[path2]
                if hash2 is None: continue

                diff = hash1 - hash2
                if diff <= 10:
                    current_duplicates.append((path2, diff))
                    image_hashes[path2] = None 

            if current_duplicates:
                has_duplicates = True
                result_tree.insert("", tk.END, values=(f"그룹 {group_id}", "원래 사진", path1))
                for dup_path, diff_score in current_duplicates:
                    result_tree.insert("", tk.END, values=(f"그룹 {group_id}", f"유사도 차이: {diff_score}", dup_path))
                group_id += 1

        progress_bar['value'] = 100
        if has_duplicates:
            status_label.config(text="🎯 탐색 완료!")
            messagebox.showinfo("완료", "중복 및 유사 파일을 성공적으로 찾아냈습니다!")
        else:
            status_label.config(text="🎉 중복 없음")
            messagebox.showinfo("완료", "비슷한 이미지가 없습니다!")
            
    except Exception as e:
        tb_text = traceback.format_exc()
        status_label.config(text="❌ 스캔 에러 발생")
        write_log_and_show_error("검색 엔진 가동 실패", str(e), tb_text)

# --- [ 기능 4: 이미지 실시간 미리보기 ] ---
def on_tree_select(event):
    try:
        selected_items = result_tree.selection()
        if not selected_items:
            return
            
        item_values = result_tree.item(selected_items[0], 'values')
        file_path = item_values[2]
        
        img = None
        
        if " ➔ [ZIP] " in file_path:
            try:
                zip_path, member_path = file_path.split(" ➔ [ZIP] ")
                with zipfile.ZipFile(zip_path, 'r') as z:
                    with z.open(member_path) as f:
                        img = Image.open(BytesIO(f.read()))
            except Exception as e:
                preview_label.config(image='', text=f"❌ ZIP 이미지 로드 실패\n({e})")
                return
        else:
            try:
                img = Image.open(file_path)
            except Exception as e:
                preview_label.config(image='', text=f"❌ 이미지 로드 실패\n({e})")
                return

        if img:
            img.thumbnail((250, 250))
            img_tk = ImageTk.PhotoImage(img)
            preview_label.image = img_tk 
            preview_label.config(image=img_tk, text="")
    except Exception as e:
        tb_text = traceback.format_exc()
        write_log_and_show_error("미리보기 출력 실패", str(e), tb_text)

# --- [ 기능 5: 선택한 파일 삭제 ] ---
def delete_selected_file():
    try:
        selected_items = result_tree.selection()
        if not selected_items:
            messagebox.showwarning("선택 에러", "삭제할 파일을 리스트에서 먼저 선택해 주세요.")
            return
            
        item_id = selected_items[0]
        item_values = result_tree.item(item_id, 'values')
        file_path = item_values[2]
        
        if " ➔ [ZIP] " in file_path:
            messagebox.showinfo("안내", "ZIP 압축 파일 내부의 개별 파일 삭제는 지원하지 않습니다.")
            return
            
        filename = os.path.basename(file_path)
        confirm = messagebox.askyesno("⚠️ 파일 삭제 확인", f"정말로 이 파일을 영구 삭제하시겠습니까?\n\n파일명: {filename}")
        
        if confirm:
            try:
                os.remove(file_path)
                result_tree.delete(item_id)
                preview_label.config(image='', text=f"🗑️ 파일이 완전히 삭제되었습니다.\n파일명: {filename}")
                messagebox.showinfo("성공", "파일이 성공적으로 삭제되었습니다.")
            except Exception as e:
                messagebox.showerror("삭제 에러", f"파일을 지우지 못했습니다.\n이유: {e}")
    except Exception as e:
        tb_text = traceback.format_exc()
        write_log_and_show_error("파일 삭제 로직 실패", str(e), tb_text)

# --- [ 기능 6: 실시간 테마 색상 변경 ] ---
def change_theme(theme_name):
    try:
        t = THEMES[theme_name]
        root.configure(bg=t["root_bg"])
        theme_panel.configure(bg=t["root_bg"])
        control_frame.configure(bg=t["root_bg"])
        status_label.configure(bg=t["root_bg"], fg=t["text_color"])
        theme_label.configure(bg=t["root_bg"], fg=t["text_color"])
        
        top_frame.configure(bg=t["frame_bg"], fg=t["text_color"])
        btn_frame.configure(bg=t["frame_bg"])
        left_frame.configure(bg=t["frame_bg"], fg=t["text_color"])
        right_frame.configure(bg=t["frame_bg"], fg=t["text_color"])
        
        add_btn.configure(bg=t["btn_normal"], fg=t["btn_normal_fg"])
        remove_btn.configure(bg=t["btn_normal"], fg=t["btn_normal_fg"])
        folder_listbox.configure(bg=t["root_bg"], fg=t["text_color"])
        scan_btn.configure(bg=t["btn_scan"], fg=t["btn_scan_fg"], activebackground=t["btn_scan"])
        preview_label.configure(bg=t["preview_bg"], fg=t["preview_fg"])
        
        style.configure("Custom.Treeview", background=t["tree_bg"], foreground=t["tree_fg"], fieldbackground=t["tree_field"])
        style.configure("Custom.Treeview.Heading", background=t["btn_normal"], foreground=t["btn_normal_fg"])
        result_tree.configure(style="Custom.Treeview")
    except Exception as e:
        tb_text = traceback.format_exc()
        write_log_and_show_error("테마 변경 처리 실패", str(e), tb_text)


# --- [ GUI 레이아웃 디자인 ] ---
root = tk.Tk()
# 💡 정식 릴리즈 버전 v1.0 명시!
root.title("ZipMatch v1.0")
root.geometry("1000x720")

style = ttk.Style()
style.theme_use('clam')

# 상단 옵션 패널
theme_panel = tk.Frame(root)
theme_panel.pack(fill=tk.X, padx=20, pady=(10, 0))

theme_label = tk.Label(theme_panel, text="🎨 디자인 테마 선택:", font=("맑은 고딕", 10, "bold"))
theme_label.pack(side=tk.LEFT, padx=5)

theme_var = tk.StringVar(value="✨ 모던 화이트")
theme_select = ttk.Combobox(theme_panel, textvariable=theme_var, values=list(THEMES.keys()), state="readonly", width=15)
theme_select.pack(side=tk.LEFT, padx=5)
theme_select.bind("<<ComboboxSelected>>", lambda e: change_theme(theme_var.get()))

# 1. 상단 폴더 설정 영역
top_frame = tk.LabelFrame(root, text=" 📂 대상 폴더 설정 ", font=("맑은 고딕", 10, "bold"), relief=tk.SOLID, bd=1)
top_frame.pack(fill=tk.X, padx=20, pady=10)

folder_listbox = tk.Listbox(top_frame, height=3, font=("맑은 고딕", 9), bd=1, relief=tk.SOLID, highlightthickness=0)
folder_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10), pady=10)

btn_frame = tk.Frame(top_frame)
btn_frame.pack(side=tk.RIGHT, padx=10)

add_btn = tk.Button(btn_frame, text="➕ 폴더 추가", command=add_folder, font=("맑은 고딕", 9), relief=tk.SOLID, bd=1, cursor="hand2")
add_btn.pack(fill=tk.X, pady=2, ipady=3)
remove_btn = tk.Button(btn_frame, text="❌ 폴더 삭제", command=remove_folder, font=("맑은 고딕", 9), relief=tk.SOLID, bd=1, cursor="hand2")
remove_btn.pack(fill=tk.X, pady=2, ipady=3)

# 2. 중간 컨트롤 바 영역
control_frame = tk.Frame(root)
control_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

scan_btn = tk.Button(control_frame, text="🚀 초고속 검색 시작 (Scan)", command=start_scan, font=("맑은 고딕", 10, "bold"), relief=tk.FLAT, cursor="hand2")
scan_btn.pack(side=tk.LEFT, padx=5, ipadx=15, ipady=5)

progress_bar = ttk.Progressbar(control_frame, orient="horizontal", mode="determinate")
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15)

status_label = tk.Label(control_frame, text="대기 중", font=("맑은 고딕", 10, "bold"))
status_label.pack(side=tk.RIGHT, padx=5)

# 3. 하단 메인 바디
main_body = tk.Frame(root)
main_body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

left_frame = tk.LabelFrame(main_body, text=" 📋 탐색 결과 리스트 ", font=("맑은 고딕", 10, "bold"), relief=tk.SOLID, bd=1)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

columns = ("group", "info", "path")
result_tree = ttk.Treeview(left_frame, columns=columns, show="headings")

result_tree.heading("group", text="중복 그룹")
result_tree.heading("info", text="판정 코드 / 유사도")
result_tree.heading("path", text="파일 경로 및 ZIP 내부 위치")

result_tree.column("group", width=80, anchor=tk.CENTER)
result_tree.column("info", width=120, anchor=tk.CENTER)
result_tree.column("path", width=420, anchor=tk.W)

scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=result_tree.yview)
result_tree.configure(yscrollcommand=scrollbar.set)

result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

result_tree.bind('<<TreeviewSelect>>', on_tree_select)

right_frame = tk.LabelFrame(main_body, text=" 🖼️ 실시간 이미지 뷰어 ", font=("맑은 고딕", 10, "bold"), relief=tk.SOLID, bd=1, width=300)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
right_frame.pack_propagate(False)

preview_label = tk.Label(right_frame, text="🖼️ 리스트에서 파일을 선택하면\n여기에 미리보기가 표시됩니다.", 
                         font=("맑은 고딕", 9), width=30, relief=tk.FLAT)
preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

delete_btn = tk.Button(right_frame, text="🗑️ 선택한 파일 삭제", command=delete_selected_file,
                        bg="#e53935", fg="white", font=("맑은 고딕", 10, "bold"), relief=tk.FLAT, activebackground="#c62828", cursor="hand2")
delete_btn.pack(fill=tk.X, ipady=6, padx=10, pady=(0, 10))

change_theme("✨ 모던 화이트")

root.mainloop()