import customtkinter as ctk

# --- MISMOS COLORES DEL REPRODUCTOR PRINCIPAL ---
BG_COLOR = "#0F0F1A"       
PANEL_COLOR = "#181825"    
ACCENT_COLOR = "#7F00FF"   
TEXT_COLOR = "#FFFFFF"
SUBTEXT_COLOR = "#A0A0B0"

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, is_dark_mode, volume, callback_theme, callback_volume):
        super().__init__(parent)
        self.title("Ajustes Premium - CrisHDZ")
        self.geometry("480x420")
        
        # Tema Oscuro general de la ventana
        self.configure(fg_color=BG_COLOR)
        self.attributes("-topmost", True)

        self.callback_theme = callback_theme
        self.callback_volume = callback_volume

        # --- TABVIEW (Navegación Premium) ---
        self.tabview = ctk.CTkTabview(
            self, 
            width=430, height=360,
            fg_color=PANEL_COLOR,
            segmented_button_fg_color=BG_COLOR,
            segmented_button_selected_color=ACCENT_COLOR,
            segmented_button_selected_hover_color="#9d00ff",
            text_color=TEXT_COLOR
        )
        self.tabview.pack(padx=20, pady=20, expand=True, fill="both")
        
        self.tab_ajustes = self.tabview.add("⚙️ Ajustes")
        self.tab_eq = self.tabview.add("🎚️ Ecualizador")
        self.tab_about = self.tabview.add("ℹ️ Acerca de")

        self.setup_ajustes(is_dark_mode, volume)
        self.setup_eq()
        self.setup_about()

    def setup_ajustes(self, is_dark_mode, volume):
        self.tab_ajustes.grid_columnconfigure(0, weight=1)
        
        lbl_titulo = ctk.CTkLabel(self.tab_ajustes, text="Personalización", font=("Segoe UI", 20, "bold"), text_color=ACCENT_COLOR)
        lbl_titulo.grid(row=0, column=0, pady=(15, 20))
        
        self.switch_theme = ctk.CTkSwitch(
            self.tab_ajustes, 
            text="Modo Oscuro Dinámico", 
            font=("Segoe UI", 14),
            progress_color=ACCENT_COLOR,
            command=self.cambiar_tema
        )
        if is_dark_mode: self.switch_theme.select()
        else: self.switch_theme.deselect()
        self.switch_theme.grid(row=1, column=0, pady=15)

        ctk.CTkLabel(self.tab_ajustes, text="Volumen Maestro", font=("Segoe UI", 15, "bold"), text_color=TEXT_COLOR).grid(row=2, column=0, pady=(20, 5))
        
        self.vol_slider = ctk.CTkSlider(
            self.tab_ajustes, from_=0, to=1, 
            progress_color=ACCENT_COLOR, 
            button_color=TEXT_COLOR, 
            button_hover_color=ACCENT_COLOR,
            command=self.cambiar_volumen
        )
        self.vol_slider.set(volume)
        self.vol_slider.grid(row=3, column=0, pady=10, padx=40, sticky="ew")

    def setup_eq(self):
        ctk.CTkLabel(self.tab_eq, text="Ecualizador Pro", font=("Segoe UI", 20, "bold"), text_color=ACCENT_COLOR).pack(pady=(15, 10))
        ctk.CTkLabel(self.tab_eq, text="Ajusta las frecuencias a tu gusto", font=("Segoe UI", 12), text_color=SUBTEXT_COLOR).pack(pady=(0, 15))
        
        self.frame_sliders = ctk.CTkFrame(self.tab_eq, fg_color="transparent")
        self.frame_sliders.pack(expand=True, fill="both")

        bandas = ["60Hz", "230Hz", "910Hz", "4kHz", "14kHz"]
        for i, banda in enumerate(bandas):
            self.frame_sliders.grid_columnconfigure(i, weight=1)
            s = ctk.CTkSlider(self.frame_sliders, from_=0, to=2, orientation="vertical", height=140, progress_color=ACCENT_COLOR, button_color=TEXT_COLOR)
            s.set(1.0)
            s.grid(row=0, column=i, padx=5, pady=10)
            ctk.CTkLabel(self.frame_sliders, text=banda, font=("Segoe UI", 11, "bold"), text_color=SUBTEXT_COLOR).grid(row=1, column=i)

    def setup_about(self):
        self.tab_about.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.tab_about, text="CrisHDZ Player", font=("Segoe UI", 26, "bold"), text_color=ACCENT_COLOR).grid(row=0, column=0, pady=(40, 5))
        ctk.CTkLabel(self.tab_about, text="Versión 9.5 Premium Edition", font=("Segoe UI", 15), text_color=TEXT_COLOR).grid(row=1, column=0, pady=5)
        
        texto_desc = "Desarrollado con pasión para Windows.\nDisfruta de la experiencia completa\ncon el rediseño más moderno."
        ctk.CTkLabel(self.tab_about, text=texto_desc, font=("Segoe UI", 13), text_color=SUBTEXT_COLOR, justify="center").grid(row=2, column=0, pady=25)

    def cambiar_tema(self):
        self.callback_theme(bool(self.switch_theme.get()))

    def cambiar_volumen(self, valor):
        self.callback_volume(float(valor))
