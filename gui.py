import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from foundry_log_analyzer import parse_log_file, aggregate_stats
import tkinter as tk
from datetime import datetime


def get_screen_size():
    """Returns (width, height) of the primary screen."""
    root = tk.Tk()
    root.withdraw()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.destroy()
    return width, height


def extract_dates_from_log(file_path):
    """Extracts unique dates from log file headers, returns as DD/MM/YYYY for display."""
    dates = []
    date_pattern = r"^\[(\d{1,2}/\d{1,2}/\d{4})"
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = __import__('re').search(date_pattern, line)
            if match:
                date_str = match.group(1)  # MM/DD/YYYY
                # Convert to DD/MM/YYYY for display
                try:
                    dt = datetime.strptime(date_str, '%m/%d/%Y')
                    display_date = dt.strftime('%d/%m/%Y')
                except:
                    display_date = date_str
                if display_date not in dates:
                    dates.append(display_date)
    return dates


def filter_events_by_date(events, display_date):
    """Filters events to only include those from the given DD/MM/YYYY date."""
    filtered = []
    # Convert DD/MM/YYYY back to MM/DD/YYYY for comparison with raw events
    try:
        dt = datetime.strptime(display_date, '%d/%m/%Y')
        target_date = dt.strftime('%m/%d/%Y')
    except:
        return events

    for event in events:
        if event.get('type') == 'timestamp':
            # Raw timestamp format: [MM/DD/YYYY, H:MM:SS AM/PM]
            ts = event.get('timestamp', '')
            if ts.startswith(target_date):
                filtered.append(event)
            continue
        # Include the event if we're in the right date block
        if filtered and filtered[-1].get('type') == 'timestamp':
            last_ts = filtered[-1].get('timestamp', '')
            if last_ts.startswith(target_date):
                filtered.append(event)
            elif not last_ts.startswith(target_date):
                # We've moved past the target date
                if len(filtered) > 0 and filtered[-1].get('type') == 'timestamp':
                    filtered.pop()  # remove the timestamp that started new block
                break
    return filtered


def create_window():
    """Creates and returns the main application window."""
    sg.theme("DarkBlue13")

    # Get screen size and limit window to 90% of screen
    screen_w, screen_h = get_screen_size()
    max_w = int(screen_w * 0.9)
    max_h = int(screen_h * 0.9)

    layout = [
        [sg.Text("Foundry Log Analyzer", font=("Helvetica", 16))],
        [sg.Text("Selecione o arquivo de log:")],
        [sg.Input(key="-FILE-", readonly=True, size=(40, 1)),
         sg.FileBrowse("Procurar", file_types=(("Log Files", "*.txt *.log"), ("All Files", "*.*")))],
        [sg.Button("Analisar", key="-ANALYZE-")],
        [sg.HorizontalSeparator()],
        [sg.Text("Filtrar por data:"), sg.Combo(["<Todos>"], key="-DATE_SELECT-", size=(15, 1), readonly=True, enable_events=True, disabled=True),
         sg.Text("  Personagem:"), sg.Combo(["<Todos>"], key="-CHAR_SELECT-", size=(20, 1), readonly=True, enable_events=True, disabled=True)],
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
        [sg.Canvas(key="-CHART-", size=(650, 350))],
    ]

    return sg.Window(
        "Foundry Log Analyzer",
        layout,
        finalize=True,
        size=(max_w, max_h),
        resizable=True,
    )


def draw_bar_chart(window, selected_character, all_stats):
    """Draws bar chart for selected character or all combined."""
    if not all_stats:
        return

    # Clear previous chart
    for widget in window["-CHART-"].TKCanvas.winfo_children():
        widget.destroy()

    # Create figure with correct DPI and size
    fig = plt.figure(figsize=(8, 4), dpi=80)
    ax = fig.add_subplot(111)

    if selected_character and selected_character != "<Todos>":
        # Show comparison: Player vs Total (filtered total for the date)
        total_data = all_stats.get(selected_character, {})
        labels = ["Dano\nFísico", "Dano\nMágico", "Dano\nRecebido", "Cura"]
        player_vals = [
            total_data.get("damage_caused_physical", 0),
            total_data.get("damage_caused_magical", 0),
            total_data.get("damage_received", 0),
            total_data.get("healing", 0),
        ]
        total_vals = [
            sum(s.get("damage_caused_physical", 0) for s in all_stats.values()),
            sum(s.get("damage_caused_magical", 0) for s in all_stats.values()),
            sum(s.get("damage_received", 0) for s in all_stats.values()),
            sum(s.get("healing", 0) for s in all_stats.values()),
        ]

        x = range(len(labels))
        width = 0.35
        bars1 = ax.bar([i - width/2 for i in x], player_vals, width, label=selected_character, color="#3498db")
        bars2 = ax.bar([i + width/2 for i in x], total_vals, width, label="Total", color="#95a5a6")

        ax.set_title(f"{selected_character} vs Total", fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()

        # Add value labels
        for bar, val in zip(bars1, player_vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        str(val), ha="center", va="bottom", fontsize=8)
        for bar, val in zip(bars2, total_vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        str(val), ha="center", va="bottom", fontsize=8)

        ax.set_ylabel("Valor")
        max_val = max(max(player_vals), max(total_vals)) if player_vals or total_vals else 10
        ax.set_ylim(0, max_val * 1.2)
    else:
        # Show all combined
        values = [
            sum(s.get("damage_caused_physical", 0) for s in all_stats.values()),
            sum(s.get("damage_caused_magical", 0) for s in all_stats.values()),
            sum(s.get("damage_received", 0) for s in all_stats.values()),
            sum(s.get("healing", 0) for s in all_stats.values()),
        ]
        labels = ["Dano Físico", "Dano Mágico", "Dano Recebido", "Cura"]
        bars = ax.bar(labels, values, color=["#e74c3c", "#3498db", "#e67e22", "#2ecc71"])
        ax.set_title("Estatísticas Combinadas", fontsize=10)
        ax.set_ylabel("Valor")
        max_val = max(values) if values else 10
        ax.set_ylim(0, max_val * 1.2)
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        str(val), ha="center", va="bottom", fontsize=9)

    fig.tight_layout()

    # Embed in Canvas
    canvas = window["-CHART-"]
    figure_canvas = FigureCanvasTkAgg(fig, master=canvas.TKCanvas)
    figure_canvas.draw()
    figure_canvas.get_tk_widget().pack(fill="both", expand=True)
    plt.close(fig)


def parse_and_display(window, file_path):
    """Parses log file, updates dropdowns, table, and draws chart."""
    try:
        events = parse_log_file(file_path)

        # Extract available dates (displayed as DD/MM/YYYY)
        dates = extract_dates_from_log(file_path)
        dates = ["<Todos>"] + sorted(dates, key=lambda x: datetime.strptime(x, '%d/%m/%Y'), reverse=True)

        # Store raw events for filtering
        window.metadata = {
            'events': events,
            'stats': aggregate_stats([e for e in events if e.get('type') != 'timestamp'])
        }

        # Update date dropdown
        window["-DATE_SELECT-"].update(values=dates, value="<Todos>", disabled=False)

        # Initial display (all data)
        update_display(window)

    except Exception as e:
        sg.popup(f"Erro ao analisar: {str(e)}")


def update_display(window):
    """Updates table and chart based on current filters."""
    metadata = window.metadata
    if not metadata:
        return

    selected_date = values.get("-DATE_SELECT-", "<Todos>")
    selected_char = values.get("-CHAR_SELECT-", "<Todos>")

    events = metadata['events']
    stats = metadata['stats']

    # Filter by date if not "Todos"
    if selected_date and selected_date != "<Todos>":
        filtered_events = filter_events_by_date(events, selected_date)
        # Get only actual game events (not timestamp events)
        game_events = [e for e in filtered_events if e.get('type') != 'timestamp']
        stats = aggregate_stats(game_events)
    else:
        stats = metadata['stats']

    # Update character dropdown - only show characters active in filtered data
    characters = ["<Todos>"] + list(stats.keys())
    if selected_char not in characters:
        selected_char = "<Todos>"
    window["-CHAR_SELECT-"].update(values=characters, value=selected_char, disabled=False)

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

    # Draw chart
    draw_bar_chart(window, selected_char, stats)


def main():
    """Main event loop for the GUI application."""
    window = create_window()
    global values
    values = {}

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

        if event in ("-DATE_SELECT-", "-CHAR_SELECT-"):
            if window.metadata:
                update_display(window)

    window.close()


if __name__ == "__main__":
    main()