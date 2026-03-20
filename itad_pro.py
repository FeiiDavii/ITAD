# ==============================================================================
# ITAD Pro — Sistema de Disposición Final de Activos Tecnológicos
# Basado en el diseño original, con UI mejorada y tema claro/oscuro funcional
# ==============================================================================

import os
import sys
import ctypes
import threading
import subprocess
import json
import datetime
import time
import getpass
import platform
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

# ──────────────────────────────────────────────────────────────────────────────
#  TEMAS — todos los colores en un solo lugar
# ──────────────────────────────────────────────────────────────────────────────

DARK = {
    "mode":           "Dark",
    "root_bg":        "#0F0F0F",
    "header_bg":      "#161616",
    "card_bg":        "#1A1A1A",
    "card2_bg":       "#212121",
    "input_bg":       "#111111",
    "border":         "#2C2C2C",
    "accent_red":     "#D32F2F",
    "accent_red_hov": "#B71C1C",
    "accent_blue":    "#1565C0",
    "accent_blue_hov":"#0D47A1",
    "btn_gray":       "#2C2C2C",
    "btn_gray_hov":   "#383838",
    "text_hi":        "#F5F5F5",
    "text_mid":       "#9E9E9E",
    "text_lo":        "#555555",
    "log_bg":         "#080808",
    "log_fg":         "#E0E0E0",
    "tag_head":       "#CE93D8",
    "tag_ok":         "#69F0AE",
    "tag_info":       "#40C4FF",
    "tag_warn":       "#FFD740",
    "tag_err":        "#FF5252",
    "progress_track": "#2C2C2C",
    "progress_fill":  "#1565C0",
}

LIGHT = {
    "mode":           "Light",
    "root_bg":        "#F0F2F5",
    "header_bg":      "#FFFFFF",
    "card_bg":        "#FFFFFF",
    "card2_bg":       "#F8F9FA",
    "input_bg":       "#F0F2F5",
    "border":         "#E0E0E0",
    "accent_red":     "#C62828",
    "accent_red_hov": "#B71C1C",
    "accent_blue":    "#1565C0",
    "accent_blue_hov":"#0D47A1",
    "btn_gray":       "#E8E8E8",
    "btn_gray_hov":   "#D5D5D5",
    "text_hi":        "#111111",
    "text_mid":       "#555555",
    "text_lo":        "#AAAAAA",
    "log_bg":         "#F8F9FA",
    "log_fg":         "#1F2937",
    "tag_head":       "#7B1FA2",
    "tag_ok":         "#2E7D32",
    "tag_info":       "#01579B",
    "tag_warn":       "#E65100",
    "tag_err":        "#C62828",
    "progress_track": "#E0E0E0",
    "progress_fill":  "#1565C0",
}

T = DARK  # tema activo global


# ──────────────────────────────────────────────────────────────────────────────
#  UTILIDADES
# ──────────────────────────────────────────────────────────────────────────────

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_physical_disks():
    cmd = (
        "Get-PhysicalDisk | Select-Object DeviceId,Model,Size,"
        "MediaType,BusType,SerialNumber,HealthStatus,OperationalStatus "
        "| ConvertTo-Json -Depth 2"
    )
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        startupinfo=si, text=True, encoding="utf-8", errors="replace"
    )
    out, err = proc.communicate(timeout=30)
    if proc.returncode != 0 or not out.strip():
        return []
    try:
        data = json.loads(out)
    except Exception:
        return []
    if isinstance(data, dict):
        data = [data]
    disks = []
    for d in data:
        size_gb = round(d.get("Size", 0) / (1024 ** 3), 2)
        disks.append({
            "id":      str(d.get("DeviceId", "?")),
            "model":   d.get("Model", "Desconocido").strip(),
            "serial":  d.get("SerialNumber", "N/A").strip(),
            "health":  d.get("HealthStatus", "?"),
            "status":  d.get("OperationalStatus", "?"),
            "size_gb": size_gb,
            "type":    d.get("MediaType", "N/A"),
            "bus":     d.get("BusType", "N/A"),
            "path":    f"\\\\.\\PhysicalDrive{d.get('DeviceId')}",
        })
    return sorted(disks, key=lambda x: int(x["id"]))


# ──────────────────────────────────────────────────────────────────────────────
#  HILO DE BORRADO (lógica original intacta)
# ──────────────────────────────────────────────────────────────────────────────

def wipe_process_thread(disk_data, start_btn_ref, phys_method):
    disk_id    = disk_data["id"]
    drive_path = disk_data["path"]
    block_size = 1024 * 1024
    bytes_written = 0
    operador = getpass.getuser()
    sistema  = f"{platform.system()} {platform.release()}"

    def log(msg, tag=None):
        ts = f"[{get_timestamp()}] {msg}\n"
        app.after(0, lambda m=ts, t=tag: _log_insert(m, t))

    log("══════════════════════════════════════════════════════", "head")
    log("      CERTIFICADO DE SANEAMIENTO Y DESTRUCCIÓN        ", "head")
    log("══════════════════════════════════════════════════════", "head")
    log(f"Operador Responsable : {operador}")
    log(f"Estación de Trabajo  : {sistema}")
    log(f"Fecha de Inicio      : {get_timestamp()}")
    log("──────────────────────────────────────────────────────")
    log("DATOS DEL HARDWARE AUDITADO:", "head")
    log(f"  > ID Físico      : Disco {disk_id}")
    log(f"  > Modelo         : {disk_data['model']}")
    log(f"  > Num. de Serie  : {disk_data['serial']}")
    log(f"  > Capacidad      : {disk_data['size_gb']} GB")
    log(f"  > Interfaz/Bus   : {disk_data['type']} / {disk_data['bus']}")
    log(f"  > Salud S.M.A.R.T: {disk_data['health']} ({disk_data['status']})")
    log("──────────────────────────────────────────────────────")
    log("PARÁMETROS DE DISPOSICIÓN:", "head")
    log(f"  > Borrado Lógico : Zero-Fill Directo (1 Pase)")
    log(f"  > Destino Físico : {phys_method}")
    log("══════════════════════════════════════════════════════", "head")

    start_time_global = time.time()

    try:
        log("[PASO 1] Destruyendo tabla de particiones (MBR/GPT)...", "info")
        dp_script = f"select disk {disk_id}\nclean\nexit\n"
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        dp = subprocess.Popen(
            ["diskpart"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, startupinfo=si, text=True
        )
        dp.communicate(dp_script)
        log("[OK] Tabla de particiones destruida. Disco desmontado.", "ok")

        log("[PASO 2] Abriendo acceso RAW y comenzando sobrescritura...", "info")
        with open(drive_path, "wb", buffering=0) as drive:
            empty_block = b"\x00" * block_size
            mb_counter  = 0
            lap_start   = time.time()

            while True:
                drive.write(empty_block)
                bytes_written += block_size
                mb_counter    += 1

                if mb_counter >= 1000:
                    gb_done = bytes_written / (1024 ** 3)
                    elapsed = time.time() - lap_start
                    speed   = mb_counter / elapsed if elapsed > 0 else 0
                    pct     = min(99, (gb_done / disk_data["size_gb"]) * 100) if disk_data["size_gb"] > 0 else 0
                    log(f"Progreso: {gb_done:.2f} GB  |  Velocidad: {speed:.1f} MB/s", "info")
                    app.after(0, lambda p=pct: _set_progress(p))
                    mb_counter = 0
                    lap_start  = time.time()

    except OSError:
        end_time  = time.time()
        total_min = (end_time - start_time_global) / 60
        gb_total  = bytes_written / (1024 ** 3)

        app.after(0, lambda: _set_progress(100))
        log("──────────────────────────────────────────────────────")
        log("[ÉXITO] Límite físico del disco alcanzado.", "ok")
        log("RESUMEN DE LA OPERACIÓN:", "head")
        log(f"  > Total Sobrescrito : {gb_total:.2f} GB", "ok")
        log(f"  > Tiempo Invertido  : {total_min:.1f} Minutos", "ok")
        log(f"  > Acción Requerida  : Enviar a {phys_method}.", "warn")
        log("══════════════════════════════════════════════════════", "head")
        app.after(0, lambda: messagebox.showinfo(
            "Proceso Finalizado",
            f"Saneamiento lógico completado.\n"
            f"Total: {gb_total:.2f} GB en {total_min:.1f} min.\n\n"
            f"Proceda con: {phys_method}"
        ))

    except PermissionError:
        log("[ERROR CRÍTICO] Windows denegó el acceso de escritura.", "err")
        app.after(0, lambda: messagebox.showerror("Error de Permisos",
            "Acceso denegado. Asegúrate de que el disco no está en uso\n"
            "y que la aplicación corre como Administrador."))

    except Exception as exc:
        log(f"[ERROR INESPERADO] {exc}", "err")

    finally:
        app.after(0, lambda: start_btn_ref.configure(state="normal"))
        app.after(0, lambda: _progress_label_var.set("En espera..."))


# ──────────────────────────────────────────────────────────────────────────────
#  HELPERS DE UI (accesibles desde el hilo de borrado)
# ──────────────────────────────────────────────────────────────────────────────

def _log_insert(msg, tag=None):
    log_area.configure(state="normal")
    if tag:
        log_area.insert("end", msg, tag)
    else:
        log_area.insert("end", msg)
    log_area.see("end")
    log_area.configure(state="disabled")

def _set_progress(value):
    _progress_var.set(value / 100)
    _progress_label_var.set(f"{value:.0f}%")


# ──────────────────────────────────────────────────────────────────────────────
#  LÓGICA DE INTERFAZ
# ──────────────────────────────────────────────────────────────────────────────

_disk_map = {}
_sel_disk = None
_progress_var       = None
_progress_label_var = None

def refresh_disk_list():
    global _sel_disk
    _sel_disk = None
    btn_start.configure(state="disabled")
    details_var.set("Selecciona un disco de la lista para inspeccionarlo...")
    _disk_map.clear()
    disk_menu.configure(values=["Escaneando discos..."])
    disk_menu.set("Escaneando discos...")
    app.update()

    def _scan():
        disks = get_physical_disks()
        app.after(0, lambda: _populate(disks))

    threading.Thread(target=_scan, daemon=True).start()

def _populate(disks):
    if not disks:
        disk_menu.configure(values=["No se encontraron discos"])
        disk_menu.set("No se encontraron discos")
        return
    vals = []
    for d in disks:
        txt = f"Disco {d['id']}  ·  {d['model']}  ({d['size_gb']} GB)"
        vals.append(txt)
        _disk_map[txt] = d
    disk_menu.configure(values=vals)
    disk_menu.set("— Seleccione un disco —")

def on_disk_select(value):
    global _sel_disk
    _sel_disk = _disk_map.get(value)
    if not _sel_disk:
        btn_start.configure(state="disabled")
        return
    d = _sel_disk
    details_var.set(
        f"  ID Sistema    Disco {d['id']}\n"
        f"  Modelo        {d['model']}\n"
        f"  S/N           {d['serial']}\n"
        f"  Capacidad     {d['size_gb']} GB\n"
        f"  Tecnología    {d['type']}  ·  {d['bus']}\n"
        f"  Salud SMART   {d['health']}  ({d['status']})"
    )
    btn_start.configure(state="normal")

def start_wipe():
    confirm = entry_confirm.get().strip()
    phys    = combo_method.get()

    if not _sel_disk:
        messagebox.showwarning("Atención", "Selecciona un disco primero.")
        return
    if confirm != "DESTRUIR":
        messagebox.showwarning("Confirmación requerida", "Escribe exactamente: DESTRUIR")
        return
    if phys.startswith("—"):
        messagebox.showwarning("Atención", "Selecciona un destino físico.")
        return

    msg = (
        f"¿Confirmas el borrado IRREVERSIBLE del\n\n"
        f"  Disco {_sel_disk['id']} — {_sel_disk['model']}\n"
        f"  {_sel_disk['size_gb']} GB\n\n"
        f"y su posterior: {phys}?"
    )
    if not messagebox.askyesno("CONFIRMACIÓN CRÍTICA", msg, icon="warning"):
        return

    btn_start.configure(state="disabled")
    log_area.configure(state="normal")
    log_area.delete("1.0", "end")
    log_area.configure(state="disabled")
    _set_progress(0)

    threading.Thread(
        target=wipe_process_thread,
        args=(_sel_disk, btn_start, phys),
        daemon=True
    ).start()

def export_log():
    content = log_area.get("1.0", "end").strip()
    if not content:
        messagebox.showinfo("Exportar", "El log está vacío.")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Texto", "*.txt")],
        initialfile=f"ITAD_Cert_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Exportado", "Certificado guardado correctamente.")


# ──────────────────────────────────────────────────────────────────────────────
#  APLICAR TEMA — recorre todos los widgets y actualiza sus colores
# ──────────────────────────────────────────────────────────────────────────────

def apply_theme():
    # Raíz y separadores estructurales
    app.configure(fg_color=T["root_bg"])
    header_frame.configure(fg_color=T["header_bg"])
    header_sep.configure(fg_color=T["border"])

    # Textos de cabecera
    title_lbl.configure(text_color=T["text_hi"])
    subtitle_lbl.configure(text_color=T["text_mid"])
    theme_btn.configure(
        fg_color=T["btn_gray"], hover_color=T["btn_gray_hov"],
        text_color=T["text_hi"],
        text="🌙  Oscuro" if T["mode"] == "Light" else "☀  Claro"
    )

    # Tarjetas
    left_card.configure(fg_color=T["card_bg"])
    right_card.configure(fg_color=T["card_bg"])
    bottom_card.configure(fg_color=T["card_bg"])

    # Labels de sección y metadatos
    lbl_hw.configure(text_color=T["text_hi"])
    lbl_disco.configure(text_color=T["text_mid"])
    lbl_verif.configure(text_color=T["text_hi"])
    lbl_dest.configure(text_color=T["text_mid"])
    lbl_confirm.configure(text_color=T["text_mid"])
    log_title_lbl.configure(text_color=T["text_hi"])

    # Menú de disco
    disk_menu.configure(
        fg_color=T["input_bg"],
        button_color=T["accent_blue"],
        button_hover_color=T["accent_blue_hov"],
        dropdown_fg_color=T["card2_bg"],
        text_color=T["text_hi"],
        dropdown_text_color=T["text_hi"],
    )

    # Botones neutrales
    btn_refresh.configure(fg_color=T["btn_gray"], hover_color=T["btn_gray_hov"], text_color=T["text_hi"])
    btn_export.configure(fg_color=T["btn_gray"], hover_color=T["btn_gray_hov"], text_color=T["text_hi"])
    btn_clear.configure(fg_color=T["btn_gray"], hover_color=T["btn_gray_hov"], text_color=T["text_hi"])

    # Bloque de detalles
    details_lbl.configure(fg_color=T["card2_bg"], text_color=T["text_mid"])
    inner_sep.configure(fg_color=T["border"])

    # Menú destino físico
    combo_method.configure(
        fg_color=T["input_bg"],
        button_color=T["btn_gray"],
        button_hover_color=T["btn_gray_hov"],
        dropdown_fg_color=T["card2_bg"],
        text_color=T["text_hi"],
        dropdown_text_color=T["text_hi"],
    )

    # Entry
    entry_confirm.configure(
        fg_color=T["input_bg"], text_color=T["text_hi"],
        border_color=T["border"], placeholder_text_color=T["text_lo"]
    )

    # Botón destruir
    btn_start.configure(fg_color=T["accent_red"], hover_color=T["accent_red_hov"])

    # Progreso
    progress_bar.configure(fg_color=T["progress_track"], progress_color=T["progress_fill"])
    progress_lbl.configure(text_color=T["text_mid"])

    # Log
    log_area.configure(fg_color=T["log_bg"], text_color=T["log_fg"])
    log_area.tag_config("head", foreground=T["tag_head"])
    log_area.tag_config("ok",   foreground=T["tag_ok"])
    log_area.tag_config("info", foreground=T["tag_info"])
    log_area.tag_config("warn", foreground=T["tag_warn"])
    log_area.tag_config("err",  foreground=T["tag_err"])

def toggle_theme():
    global T
    T = LIGHT if T is DARK else DARK
    ctk.set_appearance_mode(T["mode"])
    apply_theme()


# ──────────────────────────────────────────────────────────────────────────────
#  UAC
# ──────────────────────────────────────────────────────────────────────────────

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        " ".join(f'"{a}"' for a in sys.argv), None, 1
    )
    sys.exit(0)


# ──────────────────────────────────────────────────────────────────────────────
#  CONSTRUCCIÓN DE LA INTERFAZ
# ──────────────────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("ITAD Pro — Saneamiento y Destrucción de Activos")
app.geometry("960x720")
app.minsize(820, 620)
app.configure(fg_color=T["root_bg"])

F_TITLE = ctk.CTkFont(family="Segoe UI", size=17, weight="bold")
F_SUB   = ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
F_BODY  = ctk.CTkFont(family="Segoe UI", size=12)
F_SMALL = ctk.CTkFont(family="Segoe UI", size=11)
F_MONO  = ctk.CTkFont(family="Consolas", size=11)
F_BTN   = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")

# ── CABECERA ──────────────────────────────────────────────────────────────────
header_frame = ctk.CTkFrame(app, fg_color=T["header_bg"], corner_radius=0, height=56)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

title_lbl = ctk.CTkLabel(header_frame, text="ITAD Pro", font=F_TITLE, text_color=T["text_hi"])
title_lbl.pack(side="left", padx=(20, 8))

subtitle_lbl = ctk.CTkLabel(
    header_frame,
    text="Sistema de Saneamiento y Disposición Final de Activos",
    font=F_SMALL, text_color=T["text_mid"]
)
subtitle_lbl.pack(side="left")

theme_btn = ctk.CTkButton(
    header_frame, text="☀  Claro", width=100, height=30, font=F_SMALL,
    fg_color=T["btn_gray"], hover_color=T["btn_gray_hov"], text_color=T["text_hi"],
    command=toggle_theme
)
theme_btn.pack(side="right", padx=20)

header_sep = ctk.CTkFrame(app, fg_color=T["border"], height=1)
header_sep.pack(fill="x")

# ── CONTENEDOR PRINCIPAL ──────────────────────────────────────────────────────
main = ctk.CTkFrame(app, fg_color="transparent")
main.pack(fill="both", expand=True, padx=16, pady=12)

# ── TARJETA IZQUIERDA ─────────────────────────────────────────────────────────
left_card = ctk.CTkFrame(main, fg_color=T["card_bg"], corner_radius=12, width=310)
left_card.pack(side="left", fill="both", padx=(0, 8))
left_card.pack_propagate(False)

lbl_hw = ctk.CTkLabel(left_card, text="Hardware Detectado", font=F_SUB, text_color=T["text_hi"])
lbl_hw.pack(anchor="w", padx=20, pady=(20, 4))

lbl_disco = ctk.CTkLabel(left_card, text="Disco Físico", font=F_SMALL, text_color=T["text_mid"])
lbl_disco.pack(anchor="w", padx=20, pady=(6, 2))

disk_menu = ctk.CTkOptionMenu(
    left_card, font=F_BODY, width=270,
    fg_color=T["input_bg"],
    button_color=T["accent_blue"],
    button_hover_color=T["accent_blue_hov"],
    dropdown_fg_color=T["card2_bg"],
    text_color=T["text_hi"],
    dropdown_text_color=T["text_hi"],
    values=["Inicializando..."],
    command=on_disk_select
)
disk_menu.pack(padx=20, pady=4, fill="x")

btn_refresh = ctk.CTkButton(
    left_card, text="↻  Actualizar Escaneo", font=F_SMALL, height=32,
    fg_color=T["btn_gray"], hover_color=T["btn_gray_hov"], text_color=T["text_hi"],
    command=refresh_disk_list
)
btn_refresh.pack(padx=20, pady=(4, 16), fill="x")

# ── TARJETA DERECHA ───────────────────────────────────────────────────────────
right_card = ctk.CTkFrame(main, fg_color=T["card_bg"], corner_radius=12)
right_card.pack(side="right", fill="both", expand=True)

lbl_verif = ctk.CTkLabel(right_card, text="Verificación y Ejecución", font=F_SUB, text_color=T["text_hi"])
lbl_verif.pack(anchor="w", padx=20, pady=(20, 4))

details_var = tk.StringVar(value="Selecciona un disco de la lista para inspeccionarlo...")
details_lbl = ctk.CTkLabel(
    right_card, textvariable=details_var,
    font=F_MONO, justify="left",
    text_color=T["text_mid"], fg_color=T["card2_bg"],
    corner_radius=8
)
details_lbl.pack(fill="x", padx=20, pady=(0, 12), ipady=10, ipadx=12)

inner_sep = ctk.CTkFrame(right_card, fg_color=T["border"], height=1)
inner_sep.pack(fill="x", padx=20, pady=(0, 12))

lbl_dest = ctk.CTkLabel(right_card, text="Destino Físico del Hardware", font=F_SMALL, text_color=T["text_mid"])
lbl_dest.pack(anchor="w", padx=20, pady=(0, 2))

combo_method = ctk.CTkOptionMenu(
    right_card, font=F_BODY,
    fg_color=T["input_bg"],
    button_color=T["btn_gray"],
    button_hover_color=T["btn_gray_hov"],
    dropdown_fg_color=T["card2_bg"],
    text_color=T["text_hi"],
    dropdown_text_color=T["text_hi"],
    values=[
        "— Seleccione método —",
        "Trituración (Shredding)",
        "Desmagnetización (Degaussing — Solo HDD)",
        "Perforación / Deformación Física",
        "Reciclaje Certificado (e-waste)",
        "Solo Borrado Lógico (activo reutilizado)",
    ]
)
combo_method.pack(padx=20, pady=(0, 16), fill="x")

lbl_confirm = ctk.CTkLabel(right_card, text="Confirmación de Operación", font=F_SMALL, text_color=T["text_mid"])
lbl_confirm.pack(anchor="w", padx=20, pady=(0, 2))

entry_confirm = ctk.CTkEntry(
    right_card,
    placeholder_text="Escribe  DESTRUIR  para habilitar el botón",
    justify="center", font=F_BODY,
    fg_color=T["input_bg"], text_color=T["text_hi"],
    border_color=T["border"], placeholder_text_color=T["text_lo"]
)
entry_confirm.pack(padx=20, pady=(0, 12), fill="x")

btn_start = ctk.CTkButton(
    right_card, text="⚠   INICIAR DESTRUCCIÓN", font=F_BTN, height=44,
    fg_color=T["accent_red"], hover_color=T["accent_red_hov"],
    text_color="#FFFFFF", state="disabled", command=start_wipe
)
btn_start.pack(padx=20, pady=(0, 16), fill="x")

# Progreso
_progress_var       = tk.DoubleVar(value=0)
_progress_label_var = tk.StringVar(value="En espera...")

prog_row = ctk.CTkFrame(right_card, fg_color="transparent")
prog_row.pack(fill="x", padx=20, pady=(0, 4))

progress_bar = ctk.CTkProgressBar(
    prog_row, variable=_progress_var,
    fg_color=T["progress_track"], progress_color=T["progress_fill"],
    height=6, corner_radius=3
)
progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
progress_bar.set(0)

progress_lbl = ctk.CTkLabel(
    prog_row, textvariable=_progress_label_var,
    font=F_SMALL, text_color=T["text_mid"], width=50
)
progress_lbl.pack(side="right")

btn_export = ctk.CTkButton(
    right_card, text="📄  Exportar Certificado .txt", font=F_SMALL, height=30,
    fg_color=T["btn_gray"], hover_color=T["btn_gray_hov"], text_color=T["text_hi"],
    command=export_log
)
btn_export.pack(padx=20, pady=(4, 20), anchor="e")

# ── LOG ───────────────────────────────────────────────────────────────────────
bottom_card = ctk.CTkFrame(app, fg_color=T["card_bg"], corner_radius=12)
bottom_card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

log_hdr = ctk.CTkFrame(bottom_card, fg_color="transparent")
log_hdr.pack(fill="x", padx=20, pady=(12, 4))

log_title_lbl = ctk.CTkLabel(log_hdr, text="Registro de Auditoría en Vivo", font=F_SUB, text_color=T["text_hi"])
log_title_lbl.pack(side="left")

btn_clear = ctk.CTkButton(
    log_hdr, text="Limpiar", font=F_SMALL, width=70, height=26,
    fg_color=T["btn_gray"], hover_color=T["btn_gray_hov"], text_color=T["text_hi"],
    command=lambda: (
        log_area.configure(state="normal"),
        log_area.delete("1.0", "end"),
        log_area.configure(state="disabled")
    )
)
btn_clear.pack(side="right")

log_area = ctk.CTkTextbox(
    bottom_card, font=F_MONO, state="disabled",
    wrap="word", fg_color=T["log_bg"], text_color=T["log_fg"],
    corner_radius=8
)
log_area.pack(fill="both", expand=True, padx=20, pady=(4, 16))

log_area.tag_config("head", foreground=T["tag_head"])
log_area.tag_config("ok",   foreground=T["tag_ok"])
log_area.tag_config("info", foreground=T["tag_info"])
log_area.tag_config("warn", foreground=T["tag_warn"])
log_area.tag_config("err",  foreground=T["tag_err"])

# ── ARRANQUE ──────────────────────────────────────────────────────────────────
app.after(900, refresh_disk_list)
app.mainloop()
