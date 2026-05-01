import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from foundry_log_analyzer import parse_log_file, aggregate_stats
import tkinter as tk


def get_screen_size():
    """Returns (width, height) of the primary screen."""
    root = tk.Tk()
    root.withdraw()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height


def create_window():
    """Creates and returns the main application window."""
    sg.theme("DarkBlue13")

    # Get screen size and limit window to 90% of screen
    screen_w, screen_h = get_screen_size()
    max_w = int(screen_w * 0.9)
    max_h = int(screen_h * 0.9)

    character_list = ["<Todos>"]

    layout = [
        [sg.Text("Foundry Log Analyzer", font=("Helvetica", 16))],
        [sg.Text("Selecione o arquivo de log:")],
        [sg.Input(key="-FILE-", readonly=True, size=(40, 1)),
         sg.FileBrowse("Procurar", file_types=(("Log Files", "*.txt *.log"), ("All Files", "*.*")))],
        [sg.Button("Analisar", key="-ANALYZE-")],
        [sg.HorizontalSeparator()],
        [sg.Text("Personagem:")],
        [sg.Combo(character_list, key="-CHAR_SELECT-", size=(25, 1), readonly=True, enable_events=True)],
        [sg.HorizontalSeparator()],
        [sg.Text("Dados:", font=("Helvetica", 12))],
        [sg.Table(
            headings=["Personagem", "Dano Físico", "Dano Mágico", "Dano Recebido", "Cura"],
            key="-TABLE-",
            values=[],
            num_rows=8,
            auto_size_columns=True,
            justification="left",
            alternating_row_color="gray30",
        )],
        [sg.HorizontalSeparator()],
        [sg.Text("Gráfico:", font=("Helvetica", 12))],
        [sg.Canvas(key="-CHART-", size=(550, 250))],
    ]

    return sg.Window(
        "Foundry Log Analyzer",
        layout,
        finalize=True,
        size=(max_w, max_h),
        resizable=True,
    )


def draw_bar_chart(window, selected_character):
    """Draws bar chart for selected character or all combined."""
    stats = window.metadata
    if not stats:
        return

    # Get data
    if selected_character and selected_character != "<Todos>":
        data = stats.get(selected_character, {})
        labels = ["Dano Físico", "Dano Mágico", "Dano Recebido", "Cura"]
        values = [
            data.get("damage_caused_physical", 0),
            data.get("damage_caused_magical", 0),
            data.get("damage_received", 0),
            data.get("healing", 0),
        ]
        title = f"Estatísticas de {selected_character}"
    else:
        labels = ["Dano Físico", "Dano Mágico", "Dano Recebido", "Cura"]
        values = [
            sum(s.get("damage_caused_physical", 0) for s in stats.values()),
            sum(s.get("damage_caused_magical", 0) for s in stats.values()),
            sum(s.get("damage_received", 0) for s in stats.values()),
            sum(s.get("healing", 0) for s in stats.values()),
        ]
        title = "Estatísticas Combinadas"

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 3))
    bars = ax.bar(labels, values, color=["#e74c3c", "#3498db", "#e67e22", "#2ecc71"])
    ax.set_title(title, fontsize=10)
    ax.set_ylabel("Valor")
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    str(val), ha="center", va="bottom", fontsize=8)
    plt.tight_layout()

    # Embed in Canvas
    canvas = window["-CHART-"]
    figure_canvas = FigureCanvasTkAgg(fig, master=canvas.TKCanvas)
    figure_canvas.draw()
    figure_canvas.get_tk_widget().pack(fill="both", expand=True)


def parse_and_display(window, file_path):
    """Parses log file, updates dropdown, table, and draws chart."""
    try:
        events = parse_log_file(file_path)
        stats = aggregate_stats(events)

        # Update dropdown
        characters = ["<Todos>"] + list(stats.keys())
        window["-CHAR_SELECT-"].update(values=characters, value="<Todos>")

        # Build table rows
        table_rows = []
        for character, s in stats.items():
            table_rows.append([
                character,
                s["damage_caused_physical"],
                s["damage_caused_magical"],
                s["damage_received"],
                s["healing"],
            ])

        window["-TABLE-"].update(values=table_rows)
        window.metadata = stats

        # Draw initial chart
        draw_bar_chart(window, None)

    except Exception as e:
        sg.popup(f"Erro ao analisar: {str(e)}")


def main():
    """Main event loop for the GUI application."""
    window = create_window()

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        if event == "-ANALYZE-":
            file_path = values["-FILE-"]
            if file_path:
                parse_and_display(window, file_path)
            else:
                sg.popup("Selecione um arquivo primeiro.")

        if event == "-CHAR_SELECT-":
            selected = values["-CHAR_SELECT-"]
            if selected and window.metadata:
                draw_bar_chart(window, selected)

    window.close()


if __name__ == "__main__":
    main()