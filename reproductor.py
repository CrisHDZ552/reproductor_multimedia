import customtkinter as ctk
from pygame import mixer
from tkinter import filedialog, Canvas
from PIL import Image, ImageTk, ImageDraw
import os
import json
import time

try:
    from mutagen.mp3 import MP3
    from mutagen.easyid3 import EasyID3
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

from settings_gui import SettingsWindow

mixer.init()

# --- PALETA DE COLORES PREMIUM ---
BG_COLOR = "#0F0F1A"       # Fondo general violeta/negro muy oscuro
PANEL_COLOR = "#181825"    # Paneles e islas
ACCENT_COLOR = "#7F00FF"   # Violeta brillante eléctrico (Vampire/Neon)
TEXT_COLOR = "#FFFFFF"
SUBTEXT_COLOR = "#A0A0B0"

def generar_disco_default():
    if not os.path.exists("disco.png"):
        img = Image.new("RGBA", (300, 300), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((5, 5, 295, 295), fill="#111111", outline="#050505", width=2)
        for i in range(20, 100, 20):
            draw.ellipse((i, i, 300-i, 300-i), outline="#1e1e1e", width=1)
        draw.ellipse((100, 100, 200, 200), fill=ACCENT_COLOR)
        draw.ellipse((140, 140, 160, 160), fill=PANEL_COLOR)
        img.save("disco.png")

class CrisPlayerPremium(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CrisHDZ Player - Premium Edition")
        self.geometry("1050x700")
        self.configure(fg_color=BG_COLOR)
        
        generar_disco_default()

        # Configuración
        self.config_path = "config_reproductor.json"
        self.config = self.cargar_config()
        self.ruta_actual = self.config.get("ultima_ruta", "")
        self.volumen = self.config.get("volumen", 0.5)
        self.is_dark_mode = True
        
        # Estado de Reproducción
        self.cancion_sonando = ""
        self.canciones = []
        self.indice_actual = -1
        self.pausado = True
        
        # Barra Progreso
        self.duracion_total = 0
        self.arrastrando_slider = False 
        
        # Modos de Repetición
        self.modos_repeticion = ["PLAYLIST", "UNA_VEZ", "REPETIR_UNA"]
        self.modo_actual_index = 0
        
        # Animaciones
        self.angulo_disco = 0 
        self.animacion_disco_id = None 
        self.marquee_state = "IDLE"
        self.marquee_x = 0
        self.marquee_ticks = 0
        self.texto_ancho = 0
        
        self.ventana_ajustes = None

        mixer.music.set_volume(self.volumen)
        
        self.setup_ui()
        
        if self.ruta_actual and os.path.exists(self.ruta_actual):
            self.actualizar_biblioteca()
            
        self.animar_marquesina()
        self.actualizar_progreso() # Iniciar bucle de progreso

    def cargar_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f: return json.load(f)
            except Exception: pass
        return {"ultima_ruta": "", "volumen": 0.5}

    def guardar_config(self):
        self.config["ultima_ruta"] = self.ruta_actual
        self.config["volumen"] = mixer.music.get_volume()
        try:
            with open(self.config_path, 'w') as f: json.dump(self.config, f, indent=4)
        except Exception: pass

    def setup_ui(self):
        # GRID PRINCIPAL: 2 columnas, 2 filas
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar = ctk.CTkFrame(self, width=280, fg_color=PANEL_COLOR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        lbl_logo = ctk.CTkLabel(self.sidebar, text="🎧 CrisHDZ Player", font=("Segoe UI", 24, "bold"), text_color=ACCENT_COLOR)
        lbl_logo.pack(pady=(30, 20), padx=20, anchor="w")

        self.btn_carpeta = ctk.CTkButton(self.sidebar, text="📁 Cargar Carpeta", font=("Segoe UI", 15), 
                                         fg_color="transparent", text_color=TEXT_COLOR, hover_color="#2b2b3b", 
                                         anchor="w", command=self.cargar_carpeta)
        self.btn_carpeta.pack(fill="x", padx=15, pady=5)
        
        self.btn_ajustes = ctk.CTkButton(self.sidebar, text="⚙️ Ajustes", font=("Segoe UI", 15), 
                                         fg_color="transparent", text_color=TEXT_COLOR, hover_color="#2b2b3b", 
                                         anchor="w", command=self.abrir_ajustes)
        self.btn_ajustes.pack(fill="x", padx=15, pady=5)

        ctk.CTkFrame(self.sidebar, height=2, fg_color="#2b2b3b").pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(self.sidebar, text="TU BIBLIOTECA", font=("Segoe UI", 12, "bold"), text_color=SUBTEXT_COLOR).pack(anchor="w", padx=25)

        self.scroll_canciones = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.scroll_canciones.pack(fill="both", expand=True, padx=10, pady=10)

        # ==================== ÁREA CENTRAL ====================
        self.main_area = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure((0, 3), weight=1)

        try:
            self.imagen_original_pil = Image.open("disco.png").resize((320, 320), Image.Resampling.LANCZOS)
        except Exception:
            self.imagen_original_pil = Image.new("RGBA", (320, 320), (100, 100, 100, 255))
            
        self.imagen_disco_ctk = ImageTk.PhotoImage(self.imagen_original_pil)
        self.lbl_disco = ctk.CTkLabel(self.main_area, text="", image=self.imagen_disco_ctk)
        self.lbl_disco.grid(row=1, column=0, pady=(0, 20))

        # Canvas Marquesina
        self.canvas_nombre = Canvas(self.main_area, width=550, height=60, bg=BG_COLOR, highlightthickness=0)
        self.canvas_nombre.grid(row=2, column=0, pady=0)
        self.texto_id = self.canvas_nombre.create_text(
            275, 30, text="Explora y reproduce tu música", font=("Segoe UI", 32, "bold"), fill=TEXT_COLOR, anchor="center"
        )

        # ==================== BOTTOM BAR ====================
        self.bottom_bar = ctk.CTkFrame(self, height=110, fg_color=PANEL_COLOR, corner_radius=0)
        self.bottom_bar.grid(row=1, column=1, sticky="nsew")
        self.bottom_bar.grid_columnconfigure((0, 2), weight=1)
        self.bottom_bar.grid_columnconfigure(1, weight=2)
        
        self.frame_controles = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        self.frame_controles.grid(row=0, column=1, pady=10, sticky="nsew")
        
        self.botones_row = ctk.CTkFrame(self.frame_controles, fg_color="transparent")
        self.botones_row.pack()
        
        self.btn_anterior = ctk.CTkButton(self.botones_row, text="⏮", width=40, font=("Segoe UI", 24), fg_color="transparent", hover_color="#2b2b3b", text_color=TEXT_COLOR, command=self.cancion_anterior)
        self.btn_anterior.pack(side="left", padx=15)

        self.btn_play = ctk.CTkButton(self.botones_row, text="▶", width=55, height=55, corner_radius=30, font=("Segoe UI", 24), fg_color=TEXT_COLOR, text_color=BG_COLOR, hover_color="#e0e0e0", command=self.control_play_pause)
        self.btn_play.pack(side="left", padx=15)

        self.btn_siguiente = ctk.CTkButton(self.botones_row, text="⏭", width=40, font=("Segoe UI", 24), fg_color="transparent", hover_color="#2b2b3b", text_color=TEXT_COLOR, command=self.cancion_siguiente)
        self.btn_siguiente.pack(side="left", padx=10)
        
        self.btn_repetir = ctk.CTkButton(self.botones_row, text="🔁🎶", width=40, font=("Segoe UI", 20), fg_color="transparent", hover_color="#2b2b3b", text_color=TEXT_COLOR, command=self.toggle_repeticion)
        self.btn_repetir.pack(side="left", padx=10)

        self.progreso_row = ctk.CTkFrame(self.frame_controles, fg_color="transparent")
        self.progreso_row.pack(fill="x", pady=(15, 0))
        
        self.lbl_tiempo_actual = ctk.CTkLabel(self.progreso_row, text="00:00", font=("Segoe UI", 12, "bold"), text_color=SUBTEXT_COLOR)
        self.lbl_tiempo_actual.pack(side="left", padx=15)

        self.progreso_musica = ctk.CTkSlider(self.progreso_row, from_=0, to=100, progress_color=ACCENT_COLOR, button_color=TEXT_COLOR, button_hover_color=ACCENT_COLOR, height=14)
        self.progreso_musica.set(0)
        self.progreso_musica.pack(side="left", fill="x", expand=True)
        self.progreso_musica.bind("<ButtonPress-1>", self.on_slider_press)
        self.progreso_musica.bind("<ButtonRelease-1>", self.on_slider_release)

        self.lbl_tiempo_total = ctk.CTkLabel(self.progreso_row, text="00:00", font=("Segoe UI", 12, "bold"), text_color=SUBTEXT_COLOR)
        self.lbl_tiempo_total.pack(side="right", padx=15)
        
        self.frame_vol = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        self.frame_vol.grid(row=0, column=2, sticky="e", padx=30)
        ctk.CTkLabel(self.frame_vol, text="🔊", font=("Segoe UI", 20)).pack(side="left", padx=10)
        self.slider_volumen = ctk.CTkSlider(self.frame_vol, from_=0, to=1, width=120, progress_color=ACCENT_COLOR, button_color=TEXT_COLOR, command=self.cambiar_volumen_desde_barra)
        self.slider_volumen.set(self.volumen)
        self.slider_volumen.pack(side="left")

    def on_slider_press(self, event):
        self.arrastrando_slider = True

    def on_slider_release(self, event):
        if self.duracion_total > 0 and self.cancion_sonando:
            nuevo_segundo = self.progreso_musica.get()
            try:
                mixer.music.set_pos(nuevo_segundo) 
            except Exception:
                pass
        self.arrastrando_slider = False

    def abrir_ajustes(self):
        if self.ventana_ajustes is None or not self.ventana_ajustes.winfo_exists():
            self.ventana_ajustes = SettingsWindow(self, self.is_dark_mode, self.volumen, self.cambiar_tema, self.cambiar_volumen)
        else:
            self.ventana_ajustes.focus()

    def cambiar_tema(self, is_dark):
        self.is_dark_mode = is_dark
        if is_dark:
            ctk.set_appearance_mode("Dark")
            self.canvas_nombre.configure(bg=BG_COLOR)
            self.canvas_nombre.itemconfig(self.texto_id, fill=TEXT_COLOR)
        else:
            ctk.set_appearance_mode("Light")
            self.canvas_nombre.configure(bg="#F0F0F0")
            self.canvas_nombre.itemconfig(self.texto_id, fill="#000000")
            
    def cambiar_volumen(self, valor):
        self.volumen = valor
        mixer.music.set_volume(valor)
        self.slider_volumen.set(valor)
        self.guardar_config()
        
    def cambiar_volumen_desde_barra(self, valor):
        self.volumen = valor
        mixer.music.set_volume(valor)
        self.guardar_config()
        if self.ventana_ajustes and self.ventana_ajustes.winfo_exists():
            try:
                self.ventana_ajustes.vol_slider.set(valor)
            except Exception: pass

    def actualizar_biblioteca(self):
        for widget in self.scroll_canciones.winfo_children():
            widget.destroy()

        if not os.path.exists(self.ruta_actual): return

        archivos = os.listdir(self.ruta_actual)
        self.canciones = [f for f in archivos if f.endswith((".mp3", ".wav", ".ogg"))]
        
        for i, cancion in enumerate(self.canciones):
            titulo = cancion.replace(".mp3", "")
            artista = "Desconocido"
            
            if HAS_MUTAGEN and cancion.endswith(".mp3"):
                ruta_comp = os.path.join(self.ruta_actual, cancion)
                try:
                    audio = EasyID3(ruta_comp)
                    if 'title' in audio: titulo = audio['title'][0]
                    if 'artist' in audio: artista = audio['artist'][0]
                except Exception:
                    pass
                    
            texto_mostrar = f"{titulo} • {artista}"
            if len(texto_mostrar) > 40: texto_mostrar = texto_mostrar[:37] + "..."
            
            btn = ctk.CTkButton(
                self.scroll_canciones, text=texto_mostrar, fg_color="transparent", 
                text_color=TEXT_COLOR, hover_color="#2b2b3b", anchor="w", font=("Segoe UI", 13),
                command=lambda c=cancion, idx=i: self.reproducir_especifica(c, idx)
            )
            btn.pack(fill="x", pady=4, padx=5)

    def cargar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.ruta_actual = carpeta
            self.guardar_config()
            self.actualizar_biblioteca()

    def reproducir_especifica(self, nombre_cancion, index=-1):
        self.detener_animacion() 
        ruta_completa = os.path.join(self.ruta_actual, nombre_cancion)
        
        try:
            mixer.music.load(ruta_completa)
            mixer.music.play()
        except Exception as e:
            print("Error al cargar:", e)
            return

        self.cancion_sonando = nombre_cancion
        if index != -1:
            self.indice_actual = index
        else:
            if nombre_cancion in self.canciones:
                self.indice_actual = self.canciones.index(nombre_cancion)

        # Configurar Duración con Mutagen si está
        self.duracion_total = 0
        if HAS_MUTAGEN and nombre_cancion.endswith(".mp3"):
            try:
                self.duracion_total = MP3(ruta_completa).info.length
            except Exception: pass
        if self.duracion_total == 0:
            try:
                self.duracion_total = mixer.Sound(ruta_completa).get_length()
            except Exception: pass

        if self.duracion_total > 0:
            self.progreso_musica.configure(to=self.duracion_total)
            self.lbl_tiempo_total.configure(text=self.formatear_tiempo(self.duracion_total))

        nombre_str = nombre_cancion.replace(".mp3", "")
        self.canvas_nombre.itemconfig(self.texto_id, text=nombre_str)
        bbox = self.canvas_nombre.bbox(self.texto_id)
        self.texto_ancho = bbox[2] - bbox[0]
        
        if self.texto_ancho > 530:
            self.canvas_nombre.coords(self.texto_id, 10, 30)
            self.canvas_nombre.itemconfig(self.texto_id, anchor="w")
            self.marquee_x = 10
            self.marquee_state = "PAUSED_START"
            self.marquee_ticks = 0
            self.canvas_nombre.itemconfig(self.texto_id, text=nombre_str + "          ")
            bbox2 = self.canvas_nombre.bbox(self.texto_id)
            self.texto_ancho = bbox2[2] - bbox2[0]
        else:
            self.canvas_nombre.coords(self.texto_id, 275, 30)
            self.canvas_nombre.itemconfig(self.texto_id, anchor="center")
            self.marquee_state = "IDLE"
            
        self.pausado = False
        self.btn_play.configure(text="⏸")
        self.iniciar_animacion() 

    def mostrar_toast(self, mensaje):
        if hasattr(self, 'toast_lbl') and self.toast_lbl.winfo_exists():
            self.toast_lbl.destroy()
        
        self.toast_lbl = ctk.CTkLabel(
            self.main_area, text=mensaje, fg_color="#222233", text_color="white", 
            corner_radius=15, padx=20, pady=10, font=("Segoe UI", 15, "bold")
        )
        self.toast_lbl.place(relx=0.5, rely=0.85, anchor="center")
        self.after(2500, self.destruir_toast)

    def destruir_toast(self):
        if hasattr(self, 'toast_lbl') and self.toast_lbl.winfo_exists():
            self.toast_lbl.destroy()

    def toggle_repeticion(self):
        self.modo_actual_index = (self.modo_actual_index + 1) % 3
        modo = self.modos_repeticion[self.modo_actual_index]
        
        if modo == "PLAYLIST":
            self.btn_repetir.configure(text="🔁", text_color=TEXT_COLOR)
            self.mostrar_toast("Modo: Seguir Playlist ✔️")
        elif modo == "UNA_VEZ":
            self.btn_repetir.configure(text="▶️", text_color=SUBTEXT_COLOR)
            self.mostrar_toast("Modo: Detener al terminar ✋")
        elif modo == "REPETIR_UNA":
            self.btn_repetir.configure(text="🔂", text_color=ACCENT_COLOR)
            self.mostrar_toast("Modo: Repetir Canción 🔄")
            
    def control_play_pause(self):
        if not self.cancion_sonando: return 

        if not self.pausado:
            mixer.music.pause()
            self.pausado = True
            self.btn_play.configure(text="▶")
            self.detener_animacion() 
        else:
            mixer.music.unpause()
            self.pausado = False
            self.btn_play.configure(text="⏸")
            self.iniciar_animacion() 

    def cancion_anterior(self):
        if self.canciones and self.indice_actual > 0:
            self.reproducir_especifica(self.canciones[self.indice_actual - 1], self.indice_actual - 1)

    def cancion_siguiente(self):
        if self.canciones and self.indice_actual < len(self.canciones) - 1:
            self.reproducir_especifica(self.canciones[self.indice_actual + 1], self.indice_actual + 1)
        else:
            if self.canciones:
                self.reproducir_especifica(self.canciones[0], 0)

    def formatear_tiempo(self, segundos):
        m, s = divmod(int(segundos), 60)
        return f"{m:02d}:{s:02d}"

    def actualizar_progreso(self):
        if self.cancion_sonando and not self.pausado and not self.arrastrando_slider:
            if mixer.music.get_busy():
                pos_ms = mixer.music.get_pos()
                if pos_ms >= 0:
                    tiempo_actual = pos_ms / 1000.0
                    if self.duracion_total > 0:
                        if tiempo_actual > self.duracion_total: tiempo_actual = self.duracion_total
                        self.progreso_musica.set(tiempo_actual)
                        self.lbl_tiempo_actual.configure(text=self.formatear_tiempo(tiempo_actual))
            else:
                if self.duracion_total > 0 and self.progreso_musica.get() >= self.duracion_total - 1:
                    modo = self.modos_repeticion[self.modo_actual_index]
                    
                    if modo == "PLAYLIST":
                        self.cancion_siguiente()
                    elif modo == "REPETIR_UNA":
                        self.reproducir_especifica(self.cancion_sonando, self.indice_actual)
                    elif modo == "UNA_VEZ":
                        self.pausado = True
                        self.btn_play.configure(text="▶")
                        self.detener_animacion()
                        self.progreso_musica.set(0)
                        self.lbl_tiempo_actual.configure(text="00:00")
                
        self.after(500, self.actualizar_progreso)

    def animar_marquesina(self):
        if self.marquee_state != "IDLE":
            if self.marquee_state == "PAUSED_START":
                self.marquee_ticks += 1
                if self.marquee_ticks > 60:
                    self.marquee_state = "SCROLLING"
            elif self.marquee_state == "SCROLLING":
                self.marquee_x -= 1
                self.canvas_nombre.coords(self.texto_id, self.marquee_x, 30)
                if self.marquee_x + self.texto_ancho < 540:
                    self.marquee_state = "PAUSED_END"
                    self.marquee_ticks = 0
            elif self.marquee_state == "PAUSED_END":
                self.marquee_ticks += 1
                if self.marquee_ticks > 40:
                    self.marquee_x = 10
                    self.canvas_nombre.coords(self.texto_id, self.marquee_x, 30)
                    self.marquee_state = "PAUSED_START"
                    self.marquee_ticks = 0
        self.after(30, self.animar_marquesina)

    def iniciar_animacion(self):
        self.angulo_disco = (self.angulo_disco + 2) % 360 
        imagen_rotada = self.imagen_original_pil.rotate(-self.angulo_disco)
        self.imagen_disco_ctk = ImageTk.PhotoImage(imagen_rotada)
        self.lbl_disco.configure(image=self.imagen_disco_ctk)
        self.animacion_disco_id = self.after(30, self.iniciar_animacion)

    def detener_animacion(self):
        if self.animacion_disco_id:
            self.after_cancel(self.animacion_disco_id) 
            self.animacion_disco_id = None

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark") 
    app = CrisPlayerPremium()
    app.mainloop()