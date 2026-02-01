from IPython.display import display
import gettext
import ipywidgets as widgets
import pandas as pd
import traceback

gettext.bindtextdomain('finances', 'translations')
gettext.textdomain('finances')

_ = gettext.gettext


class Finances:

    def __init__(self) -> None:
        self.COLUMNS = [_("Name"), _("Employment (%)"),
                        _("Hourly Rate (CHF)"), _("Role")]
        # see https://en.wikipedia.org/wiki/List_of_academic_ranks
        self.ROLES = [_("Lecturer"), _("Scientific Staff"),
                      _("Research Assistant")]
        self.DEFAULT_ROLE = self.ROLES[1]

        # predefined translations
        self.ACTIONS = _("Actions")

        self.df = pd.DataFrame(columns=self.COLUMNS)

        self.column_widths = {
            self.COLUMNS[0]: "150px",
            self.COLUMNS[1]: "250px",
            self.COLUMNS[2]: "160px",
            self.COLUMNS[3]: "150px",
            self.ACTIONS: "100px"
        }

        self.sort_states = {column: None for column in self.COLUMNS}

        self.known_hourly_rates = ["55", "69", "87", "89", "103", "117"]

        self.input_widgets = {
            self.COLUMNS[0]: widgets.Text(layout=widgets.Layout(
                width=self.column_widths[self.COLUMNS[0]])),

            self.COLUMNS[1]: widgets.FloatSlider(
                min=0, max=100, step=5, value=100,
                layout=widgets.Layout(
                    width=self.column_widths[self.COLUMNS[1]])),

            self.COLUMNS[2]: widgets.Combobox(
                options=self.known_hourly_rates,
                placeholder=_("Click or type for suggestions"),
                ensure_option=False,
                layout=widgets.Layout(
                    width=self.column_widths[self.COLUMNS[2]])),

            self.COLUMNS[3]: widgets.Dropdown(
                options=self.ROLES, layout=widgets.Layout(
                    width=self.column_widths[self.COLUMNS[3]]))
        }
        self.reset_input_widgets()

        self.add_button = widgets.Button(
            description=_("Add"),
            button_style="success",
            layout=widgets.Layout(width=self.column_widths[self.ACTIONS]))

        self.sort_buttons = {}
        self.filter_widgets = {}

        for col in self.COLUMNS:
            self.filter_widgets[col] = widgets.Text(
                placeholder=_("{col} Filter").format(col=col),
                layout=widgets.Layout(width=self.column_widths[col]))
            self.filter_widgets[col].continuous_update = False
            self.sort_buttons[col] = widgets.Button(
                description="↕", layout=widgets.Layout(
                    width=self.column_widths[col]))

        for col in self.COLUMNS:
            self.sort_buttons[col].on_click(
                lambda b, c=col: self.sort_column(c))
            self.filter_widgets[col].observe(
                lambda change, c=col: self.refresh_table(), names='value')

        self.output = widgets.Output(layout=widgets.Layout(
            border="1px solid lightgray",
            height="400px",
            overflow_y="auto",
            padding="0px",
            margin="0px",
            box_sizing="border-box"
        ))

        self.output_inner = widgets.VBox(layout=widgets.Layout(padding="5px"))
        with self.output:
            display(self.output_inner)

    def reset_input_widgets(self):
        self.input_widgets[self.COLUMNS[0]].value = ""
        self.input_widgets[self.COLUMNS[1]].value = 80
        self.input_widgets[self.COLUMNS[2]].value = 69
        self.input_widgets[self.COLUMNS[3]].value = self.DEFAULT_ROLE

    def add_row(self):
        try:

            new_row = {col: self.input_widgets[col].value
                       for col in self.COLUMNS}
            self.df = pd.concat(
                [self.df, pd.DataFrame([new_row])],
                ignore_index=True)
            self.reset_input_widgets()
            self.refresh_table()

        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def sort_column(self, col):
        for c in self.sort_states:
            if c != col:
                self.sort_states[c] = None
        self.sort_states[col] = (
            self.sort_states[col] is None or
            self.sort_states[col] is False)
        self.refresh_table()

    def filter_df(self):
        temp = self.df.copy()
        for col in self.COLUMNS:
            val = self.filter_widgets[col].value
            if val:
                temp = temp[
                    temp[col].astype(str).str.contains(val, case=False)]
        for col, asc in self.sort_states.items():
            if asc is not None:
                temp = temp.sort_values(col, ascending=asc)
        return temp.reset_index(drop=True)

    def delete_row(self, idx):
        self.df = self.df.drop(index=idx).reset_index(drop=True)
        self.refresh_table()

    def refresh_table(self):
        filtered = self.filter_df()
        row_boxes = []

        # --- filter and sort rows ---
        header_widgets = []
        for col in self.COLUMNS:
            header_widgets.append(widgets.VBox(
                [self.sort_buttons[col], self.filter_widgets[col]],
                layout=widgets.Layout(align_items='center')))
        header_widgets.append(widgets.Label(""))  # dummy spacer
        row_boxes.append(widgets.HBox(
            header_widgets, layout=widgets.Layout(padding="5px")))

        # --- data lines ---
        for i, (idx, row) in enumerate(filtered.iterrows()):
            cells = []

            for col in self.COLUMNS:

                if col == self.COLUMNS[1]:
                    cell = widgets.FloatSlider(
                        value=row[col], min=0, max=100, step=5,
                        layout=widgets.Layout(width=self.column_widths[col]))

                elif col == self.COLUMNS[2]:
                    cell = widgets.Combobox(
                        value=row[col],
                        options=self.known_hourly_rates,
                        placeholder=_("Click or type for suggestions"),
                        ensure_option=False,
                        layout=widgets.Layout(
                            width=self.column_widths[self.COLUMNS[2]]))

                elif col == self.COLUMNS[3]:
                    cell = widgets.Dropdown(
                        value=row[col], options=self.ROLES,
                        layout=widgets.Layout(width=self.column_widths[col]))
                else:
                    cell = widgets.Text(
                        value=row[col],
                        layout=widgets.Layout(width=self.column_widths[col]))

                def make_update_func(idx, col):
                    def update(change):
                        self.df.at[idx, col] = change['new']
                    return update
                cell.observe(make_update_func(idx, col), names='value')
                cells.append(cell)

            # delete button
            btn = widgets.Button(
                description="🗑️", button_style="danger",
                layout=widgets.Layout(width=self.column_widths[self.ACTIONS]))
            btn.on_click(lambda b, i=idx: self.delete_row(i))
            cells.append(btn)

            row_boxes.append(widgets.HBox(
                cells, layout=widgets.Layout(padding="5px")))

        # --- Alles in output_inner anzeigen ---
        self.output_inner.children = row_boxes

        # --- Sortierpfeile aktualisieren ---
        for col in self.COLUMNS:
            asc = self.sort_states[col]
            if asc is True:
                self.sort_buttons[col].description = "↑"
            elif asc is False:
                self.sort_buttons[col].description = "↓"
            else:
                self.sort_buttons[col].description = "↕"

    def show(self):
        # --- Header für Spaltennamen ---
        # output border + output padding + padding in text fields
        header_padding = "0px " + str(1 + 5 + 8) + "px"
        header_labels = [
            widgets.Label(
                col,
                layout=widgets.Layout(
                    width=self.column_widths[col],
                    font_weight='bold',
                    padding=header_padding))
            for col in self.COLUMNS
        ]
        header_labels.append(
            widgets.Label(
                self.ACTIONS,
                layout=widgets.Layout(
                    width=self.column_widths[self.ACTIONS],
                    font_weight='bold',
                    padding=header_padding))
        )
        header_row = widgets.HBox(
            header_labels, layout=widgets.Layout(padding="5px"))

        # --- Eingabezeile ---
        # output padding + container padding
        input_padding = "5px " + str(5 + 5) + "px"
        input_row = widgets.HBox(
            list(self.input_widgets.values()) + [self.add_button],
            layout=widgets.Layout(
                border="1px solid lightblue", padding=input_padding))

        # --- Einheitlicher äußerer Container ---
        container = widgets.VBox([header_row, input_row, self.output])
        container.layout.padding = "0px"

        # --- Anzeige ---
        display(container)
        self.refresh_table()
