from IPython.display import display, HTML, clear_output
import base64
import gettext
import ipywidgets as widgets
import json
import pandas as pd
import traceback

gettext.bindtextdomain('finances', 'translations')
gettext.textdomain('finances')

_ = gettext.gettext


class Finances:

    def __init__(self) -> None:

        # keys for our file
        self.TOTAL_BUDGET_KEY = "total_budget"
        self.EMPLOYEES_KEY = "employees"

        self.upload_button = widgets.FileUpload(
            description=_("Open"), accept=".json", multiple=False)
        self.upload_button.observe(self.load_data, names="value")

        self.save_button = widgets.Button(description="💾 " + _("Save"))

        self.total_budget = widgets.FloatText(
            value=0.0,
            step=0.05,
            description=_("Total Budget (CHF):"),
            style={'description_width': 'initial'})

        self.NAME_KEY = "Name"
        self.ROLE_KEY = "Role"
        self.HOURLY_RATE_KEY = "Hourly Rate (CHF)"
        self.EMPLOYMENT_PERCENTAGE_KEY = "Employment (%)"
        self.RESEARCH_PERCENTAGE_KEY = "Research (%)"
        self.ACQUISITION_HOURS_KEY = "Acquisition (h)"

        self.COLUMNS = {
            self.NAME_KEY: _("Name"),
            self.ROLE_KEY: _("Role"),
            self.HOURLY_RATE_KEY: _("Hourly Rate (CHF)"),
            self.EMPLOYMENT_PERCENTAGE_KEY: _("Employment (%)"),
            self.RESEARCH_PERCENTAGE_KEY: _("Research (%)"),
            self.ACQUISITION_HOURS_KEY: _("Acquisition (h)")
            }
        # see https://en.wikipedia.org/wiki/List_of_academic_ranks
        self.ROLES = {
            "Lecturer": _("Lecturer"),
            "Scientific Staff": _("Scientific Staff"),
            "Research Assistant": _("Research Assistant")
            }
        self.REVERSED_ROLES = {_(k): k for k in self.ROLES}

        self.DEFAULT_ROLE = self.ROLES["Scientific Staff"]

        # predefined translations
        self.ACTIONS = _("Actions")

        self.df = pd.DataFrame(columns=self.COLUMNS.keys())

        self.column_widths = {
            self.NAME_KEY: "150px",
            self.ROLE_KEY: "110px",
            self.HOURLY_RATE_KEY: "140px",
            self.EMPLOYMENT_PERCENTAGE_KEY: "210px",
            self.RESEARCH_PERCENTAGE_KEY: "210px",
            self.ACQUISITION_HOURS_KEY: "150px",
            self.ACTIONS: "100px"
        }

        self.sort_states = {column: None for column in self.COLUMNS.keys()}

        self.known_hourly_rates = ["55", "69", "87", "89", "103", "117"]

        self.input_widgets = {
            self.NAME_KEY:
                self.get_name_text(""),
            self.ROLE_KEY:
                self.get_role_dropdown(self.DEFAULT_ROLE),
            self.HOURLY_RATE_KEY:
                self.get_hourly_rate_combobox(""),
            self.EMPLOYMENT_PERCENTAGE_KEY:
                self.get_float_slider(0, self.EMPLOYMENT_PERCENTAGE_KEY),
            self.RESEARCH_PERCENTAGE_KEY:
                self.get_float_slider(0, self.RESEARCH_PERCENTAGE_KEY),
            self.ACQUISITION_HOURS_KEY:
                self.get_acquisition_floattext(0)
        }

        self.reset_input_widgets()

        self.add_button = widgets.Button(
            description=_("Add"),
            button_style="success",
            layout=widgets.Layout(width=self.column_widths[self.ACTIONS]))

        self.sort_buttons = {}
        self.filter_widgets = {}

        for col in self.COLUMNS.keys():
            self.filter_widgets[col] = widgets.Text(
                placeholder=_("{col} Filter").format(col=self.COLUMNS[col]),
                layout=widgets.Layout(width=self.column_widths[col]))
            self.filter_widgets[col].continuous_update = False
            self.sort_buttons[col] = widgets.Button(
                description="↕", layout=widgets.Layout(
                    width=self.column_widths[col]))

        for col in self.COLUMNS.keys():
            self.sort_buttons[col].on_click(
                lambda b, c=col: self.sort_column(c))
            self.filter_widgets[col].observe(
                lambda change, c=col: self.refresh_table(), names='value')

        self.output = widgets.Output(layout=widgets.Layout(
            border="1px solid lightgray",
            overflow_y="auto",
            padding="0px",
            margin="0px",
            box_sizing="border-box"
        ))

        self.output_inner = widgets.VBox(layout=widgets.Layout(padding="5px"))
        with self.output:
            display(self.output_inner)

    def get_name_text(self, value):
        return widgets.Text(value=value, layout=widgets.Layout(
            width=self.column_widths[self.NAME_KEY]))

    def get_role_dropdown(self, value):
        return widgets.Dropdown(
            value=value,
            options=self.ROLES.values(),
            layout=widgets.Layout(width=self.column_widths[self.ROLE_KEY]))

    def get_hourly_rate_combobox(self, value):
        combobox = widgets.Combobox(
            value=value,
            options=self.known_hourly_rates,
            ensure_option=False,
            layout=widgets.Layout(
                width=self.column_widths[self.HOURLY_RATE_KEY]))
        combobox.observe(self.validate_hourly_rate, names="value")
        return combobox

    def get_float_slider(self, value, width_key):
        return widgets.FloatSlider(
            min=0, max=100, step=1, value=value,
            layout=widgets.Layout(
                width=self.column_widths[width_key]))

    def get_acquisition_floattext(self, value):
        return widgets.FloatText(
            value=value, step=0.05, layout=widgets.Layout(
                width=self.column_widths[self.ACQUISITION_HOURS_KEY]))

    def load_data(self, change):
        try:
            content = self.upload_button.value[0]["content"]
            json_str = bytes(content).decode('utf-8')
            json_data = json.loads(json_str)
            self.total_budget.value = json_data[self.TOTAL_BUDGET_KEY]
            self.df = pd.DataFrame(json_data[self.EMPLOYEES_KEY])
            self.refresh_table()
        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def save_data(self):
        data_to_export = {
            self.TOTAL_BUDGET_KEY: self.total_budget.value,
            self.EMPLOYEES_KEY: self.df.to_dict(orient='records')
        }
        json_str = json.dumps(data_to_export, indent=2)
        b64 = base64.b64encode(json_str.encode()).decode()
        html = f"""
        <a id="download-link"
           download="data.json"
           href="data:text/json;base64,{b64}"
           style="display:none;">
        </a>
        <script>
            document.getElementById('download-link').click();
        </script>
        """
        with self.download_output:
            clear_output()
            display(HTML(html))

    def reset_input_widgets(self):
        self.input_widgets[self.NAME_KEY].value = ""
        self.input_widgets[self.ROLE_KEY].value = (self.DEFAULT_ROLE)
        self.input_widgets[self.HOURLY_RATE_KEY].value = ""
        self.input_widgets[self.EMPLOYMENT_PERCENTAGE_KEY].value = 80
        self.input_widgets[self.RESEARCH_PERCENTAGE_KEY].value = 50
        self.input_widgets[self.ACQUISITION_HOURS_KEY].value = 0

    def add_row(self):
        try:
            new_row = {}
            for col in self.COLUMNS.keys():
                val = self.input_widgets[col].value
                if col == self.ROLE_KEY:
                    # add untranslated role into dataframe
                    val = self.REVERSED_ROLES.get(val, val)
                new_row[col] = val

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
        for col in self.COLUMNS.keys():
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

    def validate_hourly_rate(self, change):
        try:
            # if there is any text, it must be possible to convert to int
            if change["new"]:
                int(change["new"])
        except ValueError:
            # if the new value can't be converted to int, revert the change
            change.owner.value = change.old

    def get_cell(self, idx, row, col):

        if col == self.NAME_KEY:
            cell = self.get_name_text(row[col])

        elif col == self.ROLE_KEY:
            cell = self.get_role_dropdown(self.ROLES[row[col]])

        elif col == self.HOURLY_RATE_KEY:
            cell = self.get_hourly_rate_combobox(row[col])

        elif col == self.RESEARCH_PERCENTAGE_KEY:
            cell = self.get_float_slider(
                row[col], self.RESEARCH_PERCENTAGE_KEY)

        elif col == self.EMPLOYMENT_PERCENTAGE_KEY:
            cell = self.get_float_slider(
                row[col], self.EMPLOYMENT_PERCENTAGE_KEY)

        elif col == self.ACQUISITION_HOURS_KEY:
            cell = self.get_acquisition_floattext(row[col])

        else:
            print("Warning: unhandled col", col)

        def make_update_func(idx, col):
            def update(change):
                new_value = change['new']
                if col == self.ROLE_KEY:
                    self.df.at[idx, col] = self.REVERSED_ROLES.get(
                        new_value, new_value)
                else:
                    self.df.at[idx, col] = new_value
            return update

        cell.observe(make_update_func(idx, col), names='value')
        return cell

    def refresh_table(self):
        filtered = self.filter_df()
        row_boxes = []

        # --- filter and sort rows ---
        header_widgets = []
        for col in self.COLUMNS.keys():
            header_widgets.append(widgets.VBox(
                [self.sort_buttons[col], self.filter_widgets[col]],
                layout=widgets.Layout(align_items='center')))
        header_widgets.append(widgets.Label(""))  # dummy spacer
        row_boxes.append(widgets.HBox(
            header_widgets, layout=widgets.Layout(padding="5px")))

        # --- data lines ---
        for i, (idx, row) in enumerate(filtered.iterrows()):
            cells = []

            for col in self.COLUMNS.keys():
                cell = self.get_cell(idx, row, col)
                cells.append(cell)

            # delete button
            btn = widgets.Button(
                description="🗑️", button_style="danger",
                layout=widgets.Layout(width=self.column_widths[self.ACTIONS]))
            btn.on_click(lambda b, i=idx: self.delete_row(i))
            cells.append(btn)

            row_boxes.append(widgets.HBox(
                cells, layout=widgets.Layout(padding="0px 5px")))

        # --- show everything in output_inner ---
        self.output_inner.children = row_boxes

        # --- update sorting arrows ---
        for col in self.COLUMNS.keys():
            asc = self.sort_states[col]
            if asc is True:
                self.sort_buttons[col].description = "↑"
            elif asc is False:
                self.sort_buttons[col].description = "↓"
            else:
                self.sort_buttons[col].description = "↕"

    def show(self):

        # invisible output for triggering download
        self.download_output = widgets.Output()

        # load and save buttons
        button_row = widgets.HBox(
            [self.upload_button, self.save_button, self.download_output],
            layout=widgets.Layout(padding="5px"))

        # --- column name header ---
        # output border + output padding + padding in text fields
        header_padding = "0px " + str(1 + 5 + 8) + "px"
        header_labels = [
            widgets.Label(
                self.COLUMNS[col],
                layout=widgets.Layout(
                    width=self.column_widths[col],
                    font_weight='bold',
                    padding=header_padding))
            for col in self.COLUMNS.keys()
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

        # --- input row ---
        # output padding + container padding
        input_padding = "5px " + str(5 + 5) + "px"
        input_row = widgets.HBox(
            list(self.input_widgets.values()) + [self.add_button],
            layout=widgets.Layout(
                border="1px solid lightblue", padding=input_padding))

        # --- outer container ---
        container = widgets.VBox([
            button_row,
            self.total_budget,
            header_row,
            input_row,
            self.output])
        container.layout.padding = "0px"

        # --- display program ---
        display(container)
        self.refresh_table()
