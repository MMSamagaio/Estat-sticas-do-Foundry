import PySimpleGUI as sg
from foundry_log_analyzer import parse_log_file, aggregate_stats

def create_window():
    """Creates and returns the main application window."""
    sg.theme("DarkBlue13")

    layout = [
        [sg.Text("Foundry Log Analyzer", font=("Helvetica", 16))],
        [sg.Text("Selecione o arquivo de log:")],
        [sg.Input(key="-FILE-", readonly=True, size=(60, 1)),
         sg.FileBrowse("Procurar", file_types=(("Log Files", "*.txt *.log"), ("All Files", "*.*")))],
        [sg.Button("Analisar", key="-ANALYZE-")],
        [sg.HorizontalSeparator()],
        [sg.Text("Resultados:", font=("Helvetica", 12))],
        [sg.Multiline(key="-OUTPUT-", size=(70, 20), disabled=True, autoscroll=True)],
    ]

    return sg.Window("Foundry Log Analyzer", layout, finalize=True)


def parse_and_display(window, file_path):
    """Parses log file and updates the output Multiline element."""
    try:
        events = parse_log_file(file_path)
        stats = aggregate_stats(events)

        output_lines = []
        output_lines.append("Resumo da Sessão:\n")
        output_lines.append("-" * 20 + "\n\n")

        for character, s in stats.items():
            output_lines.append(f"Personagem: {character}")
            output_lines.append(f"  - Dano Causado:")
            output_lines.append(f"    - Físico: {s['damage_caused_physical']}")
            output_lines.append(f"    - Mágico: {s['damage_caused_magical']}")
            output_lines.append(f"  - Dano Recebido: {s['damage_received']}")
            output_lines.append(f"  - Cura Realizada: {s['healing']}")
            output_lines.append("")

        window["-OUTPUT-"].update("".join(output_lines))
    except Exception as e:
        window["-OUTPUT-"].update(f"Erro ao analisar: {str(e)}")


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
                window["-OUTPUT-"].update("Selecione um arquivo primeiro.")

    window.close()


if __name__ == "__main__":
    main()