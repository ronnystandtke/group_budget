from Calculations import Calculations
from FileHandler import FileHandler
from IPython.display import display, HTML
import gettext
import ipywidgets as widgets
import pandas as pd
import traceback

gettext.bindtextdomain('finances', 'translations')
gettext.textdomain('finances')

_ = gettext.gettext


class Finances:

    def __init__(self) -> None:

        self.calculations = Calculations()
        self.file_handler = FileHandler()

        # keys for our file
        self.TOTAL_BUDGET_KEY = "total_budget"
        self.EMPLOYEES_KEY = "employees"

        self.upload_button = widgets.FileUpload(
            description=_("Open"), accept=".json", multiple=False)
        self.upload_button.observe(self.load_data, names="value")

        self.save_button = widgets.Button(description="💾 " + _("Save"))
        self.save_button.on_click(lambda b: self.save_data())

        finances_description_width = "210px"
        finances_widget_width = "400px"
        finances_style = {'description_width': finances_description_width}
        finances_layout = widgets.Layout(
                width=finances_widget_width,
                justify_content='flex-end',
                text_align='right')

        self.total_budget = widgets.FloatText(
            value=0.0,
            step=0.05,
            description=_("Total Budget (CHF):"),
            style=finances_style,
            layout=finances_layout)

        self.total_budget.observe(
            lambda change: self.update_remaining_budget(),
            names="value"
        )

        self.acquisition_expenses = widgets.FloatText(
            disabled=True,
            description=_("Acquisition Costs (CHF):"),
            style=finances_style,
            layout=finances_layout)

        self.administrative_expenses = widgets.FloatText(
            disabled=True,
            description=_("Administative Costs (CHF):"),
            style=finances_style,
            layout=finances_layout)

        self.remaining_budget = widgets.FloatText(
            disabled=True,
            description=_("Remaining Budget (CHF):"),
            style=finances_style,
            layout=widgets.Layout(width=finances_widget_width))

        self.NAME_KEY = "Name"
        self.ROLE_KEY = "Role"
        self.HOURLY_RATE_KEY = "Hourly Rate (CHF)"
        self.EMPLOYMENT_PERCENTAGE_KEY = "Employment (%)"
        self.RESEARCH_PERCENTAGE_KEY = "Research (%)"
        self.ACQUISITION_HOURS_KEY = "Acquisition (h)"
        self.ACQUISITION_COSTS_KEY = "Acquisition Costs (CHF)"
        self.ADMINISTRATION_HOURS_KEY = "Administration (h)"
        self.ADMINISTRATION_COSTS_KEY = "Administration Costs (CHF)"

        self.COLUMNS = {
            self.NAME_KEY: _("Name"),
            self.ROLE_KEY: _("Role"),
            self.HOURLY_RATE_KEY: _("Hourly<br>Rate<br>(CHF)"),
            self.EMPLOYMENT_PERCENTAGE_KEY: _("Employment<br>(%)"),
            self.RESEARCH_PERCENTAGE_KEY: _("Research<br>(%)"),
            self.ACQUISITION_HOURS_KEY: _("Acquisition<br>(h)"),
            self.ACQUISITION_COSTS_KEY: _("Acquisition<br>Costs<br>(CHF)"),
            self.ADMINISTRATION_HOURS_KEY: _("Administration<br>(h)"),
            self.ADMINISTRATION_COSTS_KEY: (
                _("Administration<br>Costs<br>(CHF)"))
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
            self.HOURLY_RATE_KEY: "90px",
            self.EMPLOYMENT_PERCENTAGE_KEY: "210px",
            self.RESEARCH_PERCENTAGE_KEY: "210px",
            self.ACQUISITION_HOURS_KEY: "90px",
            self.ACQUISITION_COSTS_KEY: "130px",
            self.ADMINISTRATION_HOURS_KEY: "130px",
            self.ADMINISTRATION_COSTS_KEY: "130px",
            self.ACTIONS: "100px"
        }

        self.sort_states = {column: None for column in self.COLUMNS.keys()}

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
                self.get_floattext(0, self.ACQUISITION_HOURS_KEY),
            self.ACQUISITION_COSTS_KEY:
                self.get_cost_label("", self.ACQUISITION_COSTS_KEY),
            self.ADMINISTRATION_HOURS_KEY:
                self.get_cost_label("", self.ADMINISTRATION_HOURS_KEY),
            self.ADMINISTRATION_COSTS_KEY:
                self.get_cost_label("", self.ADMINISTRATION_COSTS_KEY)
        }

        self.reset_input_widgets()

        self.add_button = widgets.Button(
            description=_("Add"),
            button_style="success",
            layout=widgets.Layout(width=self.column_widths[self.ACTIONS]))
        self.add_button.on_click(lambda b: self.add_row())

        self.sort_buttons = {}
        self.filter_widgets = {}
        self.acquisition_cost_labels = {}
        self.administration_cost_labels = {}
        self.administration_hours_labels = {}

        for col in self.COLUMNS.keys():
            self.filter_widgets[col] = widgets.Text(
                placeholder=_("Filter").format(col=self.COLUMNS[col]),
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
        return widgets.Combobox(
            value=value,
            options=self.calculations.known_hourly_rates,
            ensure_option=False,
            layout=widgets.Layout(
                width=self.column_widths[self.HOURLY_RATE_KEY]))

    def get_float_slider(self, value, width_key):
        return widgets.FloatSlider(
            min=0, max=100, step=1, value=value,
            layout=widgets.Layout(
                width=self.column_widths[width_key]))

    def get_floattext(self, value, width_key):
        return widgets.FloatText(
            value=value, step=1, layout=widgets.Layout(
                width=self.column_widths[width_key]))

    def get_cost_label(self, value, width_key):
        return widgets.Label(
            value=value,
            layout=widgets.Layout(
                display="flex",
                justify_content="flex-end",
                width=self.column_widths[width_key]))

    def load_data(self, change):
        if not change["new"]:
            return

        try:
            content = self.upload_button.value[0]["content"]
            json_data = self.file_handler.load_data(content)
            self.total_budget.value = json_data[
                self.file_handler.TOTAL_BUDGET_KEY]
            self.df = pd.DataFrame(json_data[self.file_handler.EMPLOYEES_KEY])
            self.refresh_table()

            self.upload_button.value = ()
            self.upload_button._counter = 0
        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def save_data(self):
        self.file_handler.save_data(
            self.total_budget.value,
            self.sort_df(self.df),
            self.download_output)

    def reset_input_widgets(self):
        self.input_widgets[self.NAME_KEY].value = ""
        self.input_widgets[self.ROLE_KEY].value = (self.DEFAULT_ROLE)
        self.input_widgets[self.HOURLY_RATE_KEY].value = ""
        self.input_widgets[self.EMPLOYMENT_PERCENTAGE_KEY].value = 80
        self.input_widgets[self.RESEARCH_PERCENTAGE_KEY].value = 50
        self.input_widgets[self.ACQUISITION_HOURS_KEY].value = 0

    def compute_acquisition_costs(self, row):
        return self.calculations.get_costs(
            row[self.HOURLY_RATE_KEY], row[self.ACQUISITION_HOURS_KEY])

    def compute_administration_costs(self, row):
        return self.calculations.get_costs(
            row[self.HOURLY_RATE_KEY], row[self.ADMINISTRATION_HOURS_KEY])

    def update_acquisition_costs_label(self, idx):
        if idx not in self.acquisition_cost_labels:
            return

        row = self.df.loc[idx]
        value = self.compute_acquisition_costs(row)
        self.acquisition_cost_labels[idx].value = f"{value:,.2f}"
        self.update_total_acquisition_costs()

    def update_administration_costs_label(self, idx):
        if idx not in self.administration_cost_labels:
            return

        row = self.df.loc[idx]
        value = self.compute_administration_costs(row)
        self.administration_cost_labels[idx].value = f"{value:,.2f}"
        self.update_total_administration_costs()

    def update_total_acquisition_costs(self):
        total = self.df.apply(self.compute_acquisition_costs, axis=1).sum()
        self.acquisition_expenses.value = total
        self.update_remaining_budget()

    def update_total_administration_costs(self):
        total = self.df.apply(self.compute_administration_costs, axis=1).sum()
        self.administrative_expenses.value = total
        self.update_remaining_budget()

    def update_remaining_budget(self):
        self.remaining_budget.value = self.calculations.get_remaining_budget(
            self.total_budget.value, self.acquisition_expenses.value,
            self.administrative_expenses.value)

    def add_row(self):
        try:
            new_row = {}

            for col in self.COLUMNS.keys():

                val = self.input_widgets[col].value

                if col == self.ROLE_KEY:
                    # add untranslated role into dataframe
                    val = self.REVERSED_ROLES.get(val, val)

                if col == self.ADMINISTRATION_HOURS_KEY:
                    employment_percentage = self.input_widgets[
                        self.EMPLOYMENT_PERCENTAGE_KEY].value
                    val = self.calculations.get_administration_hours(
                        employment_percentage)

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
                    temp[col].astype(str).str.contains(val, case=False)
                ]

        return self.sort_df(temp)

    def sort_df(self, df):
        temp = df.copy()

        for col, asc in self.sort_states.items():
            if asc is not None:

                if col == self.ROLE_KEY:
                    # sort by visible / translated role name
                    temp = temp.sort_values(
                        col,
                        ascending=asc,
                        key=lambda s: s.map(
                            lambda r: self.ROLES.get(r, r)
                        )
                    )

                elif col in (self.HOURLY_RATE_KEY,
                             self.ADMINISTRATION_HOURS_KEY):
                    temp = temp.sort_values(
                        col,
                        ascending=asc,
                        key=lambda s: pd.to_numeric(s, errors="coerce")
                    )

                elif col == self.ACQUISITION_COSTS_KEY:
                    costs = temp.apply(
                        self.compute_acquisition_costs, axis=1)
                    temp = temp.loc[costs.sort_values(ascending=asc).index]

                elif col == self.ADMINISTRATION_COSTS_KEY:
                    costs = temp.apply(
                        self.compute_administration_costs, axis=1)
                    temp = temp.loc[costs.sort_values(ascending=asc).index]

                else:
                    temp = temp.sort_values(col, ascending=asc)

        return temp

    def delete_row(self, idx):
        self.df = self.df.drop(index=idx)
        self.refresh_table()

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
            cell = self.get_floattext(row[col], self.ACQUISITION_HOURS_KEY)

        elif col == self.ACQUISITION_COSTS_KEY:
            value = self.compute_acquisition_costs(row)
            cell = self.get_cost_label(
                f"{value:,.2f}", self.ACQUISITION_COSTS_KEY)
            self.acquisition_cost_labels[idx] = cell

        elif col == self.ADMINISTRATION_HOURS_KEY:
            try:
                value = float(row[col])
                text = f"{value:.2f}"
            except Exception:
                text = "0.00"
            cell = self.get_cost_label(text, self.ADMINISTRATION_HOURS_KEY)
            self.administration_hours_labels[idx] = cell

        elif col == self.ADMINISTRATION_COSTS_KEY:
            value = self.compute_administration_costs(row)
            cell = self.get_cost_label(
                f"{value:,.2f}", self.ADMINISTRATION_COSTS_KEY)
            self.administration_cost_labels[idx] = cell

        else:
            print("Warning: unhandled col", col)

        def make_update_func(idx, col):

            def update(change):

                new_value = change['new']

                if col == self.ROLE_KEY:
                    self.df.at[idx, col] = self.REVERSED_ROLES.get(
                        new_value, new_value)
                    return

                if col == self.HOURLY_RATE_KEY:
                    try:
                        # if there is any text
                        # it must be possible to convert to int
                        if change["new"]:
                            int(change["new"])
                    except ValueError:
                        # if the new value can't be converted to int
                        # revert the change
                        change.owner.value = change.old
                        return

                self.df.at[idx, col] = new_value

                if col == self.EMPLOYMENT_PERCENTAGE_KEY:
                    admin_hours = self.calculations.get_administration_hours(
                        new_value)
                    key = self.ADMINISTRATION_HOURS_KEY
                    self.df.at[idx, key] = admin_hours
                    if idx in self.administration_hours_labels:
                        self.administration_hours_labels[idx].value = (
                            f"{admin_hours:.2f}")
                    self.update_administration_costs_label(idx)

                # update AFTER setting the new value!
                if col in (self.HOURLY_RATE_KEY,
                           self.ACQUISITION_HOURS_KEY):
                    self.update_acquisition_costs_label(idx)

                if col in (self.HOURLY_RATE_KEY,
                           self.ADMINISTRATION_HOURS_KEY):
                    self.update_administration_costs_label(idx)

            return update

        cell.observe(make_update_func(idx, col), names='value')
        return cell

    def refresh_table(self):

        self.acquisition_cost_labels.clear()

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
        for idx, row in filtered.iterrows():
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

        self.update_total_acquisition_costs()
        self.update_total_administration_costs()
        self.update_remaining_budget()

    def get_header_widget(self, text, widht_key):
        # output border + output padding + padding in text fields
        header_padding = "0px " + str(1 + 5 + 8) + "px"
        return widgets.HTML(
                value=(
                    "<div style='text-align:center;line-height:1.0;'>"
                    f"<b>{text}</b>"
                    "</div>"
                ),
                layout=widgets.Layout(
                    width=self.column_widths[widht_key],
                    padding=header_padding,
                    text_align="center"
                ),
                _dom_classes=["compact-header"]
            )

    def show(self):

        display(HTML("""
        <style>
            .compact-header {
                --jp-widgets-inline-height: 18px;
            }
        </style>
        """))
        # invisible output for triggering download
        self.download_output = widgets.Output()

        # load and save buttons
        button_row = widgets.HBox(
            [self.upload_button, self.save_button, self.download_output],
            layout=widgets.Layout(padding="5px"))

        # --- column name header ---
        header_labels = [
            self.get_header_widget(self.COLUMNS[col], col)
            for col in self.COLUMNS.keys()
        ]
        header_labels.append(
            self.get_header_widget(self.ACTIONS, self.ACTIONS)
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
            self.acquisition_expenses,
            self.administrative_expenses,
            self.remaining_budget,
            header_row,
            input_row,
            self.output])
        container.layout.padding = "0px"

        # --- display program ---
        display(container)
        self.refresh_table()
