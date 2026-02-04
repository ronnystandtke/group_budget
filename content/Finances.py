from Calculations import Calculations
from FileHandler import FileHandler
from Visualization import Visualization
from IPython.display import display, HTML
import gettext
import ipywidgets as widgets
import pandas as pd
import traceback

gettext.bindtextdomain('finances', 'translations')
gettext.textdomain('finances')

_ = gettext.gettext

# fixing the order of the df:
# finances.df = finances.df.reindex(columns=finances.COLUMNS.keys())


class Finances:

    def __init__(self) -> None:

        self.calculations = Calculations()
        self.file_handler = FileHandler()

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
        self.total_budget.observe(
            lambda change: self.refresh_visualization(),
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
        self.ANNUAL_WORKING_HOURS_KEY = "Annual Working Hours (h)"
        self.RESEARCH_PERCENTAGE_KEY = "Research (%)"
        self.RESEARCH_HOURS_KEY = "Research (h)"
        self.ACQUISITION_HOURS_KEY = "Acquisition (h)"
        self.ACQUISITION_COSTS_KEY = "Acquisition (CHF)"
        self.ADMINISTRATION_HOURS_KEY = "Administration (h)"
        self.ADMINISTRATION_COSTS_KEY = "Administration (CHF)"
        self.PUBLIC_FUNDS_KEY = "Public Funds (CHF)"

        self.COLUMNS = {
            self.NAME_KEY: _("Name"),
            self.ROLE_KEY: _("Role"),
            self.HOURLY_RATE_KEY: _("Hourly<br>Rate<br>(CHF)"),
            self.EMPLOYMENT_PERCENTAGE_KEY: _("Employment<br>(%)"),
            self.ANNUAL_WORKING_HOURS_KEY:
                _("Annual<br>Working<br>Hours<br>(h)"),
            self.RESEARCH_PERCENTAGE_KEY: _("Research<br>(%)"),
            self.RESEARCH_HOURS_KEY: _("Research<br>(h)"),
            self.ACQUISITION_HOURS_KEY: _("Acquisition<br>(h)"),
            self.ACQUISITION_COSTS_KEY: _("Acquisition<br>(CHF)"),
            self.ADMINISTRATION_HOURS_KEY: _("Administration<br>(h)"),
            self.ADMINISTRATION_COSTS_KEY: (
                _("Administration<br>(CHF)")),
            self.PUBLIC_FUNDS_KEY: _("Public<br>Funds<br>(CHF)")
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
            self.EMPLOYMENT_PERCENTAGE_KEY: "190px",
            self.ANNUAL_WORKING_HOURS_KEY: "55px",
            self.RESEARCH_PERCENTAGE_KEY: "190px",
            self.RESEARCH_HOURS_KEY: "100px",
            self.ACQUISITION_HOURS_KEY: "90px",
            self.ACQUISITION_COSTS_KEY: "70px",
            self.ADMINISTRATION_HOURS_KEY: "120px",
            self.ADMINISTRATION_COSTS_KEY: "120px",
            self.PUBLIC_FUNDS_KEY: "120px",
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
            self.ANNUAL_WORKING_HOURS_KEY:
                self.get_cost_label("", self.ANNUAL_WORKING_HOURS_KEY),
            self.RESEARCH_PERCENTAGE_KEY:
                self.get_float_slider(0, self.RESEARCH_PERCENTAGE_KEY),
            self.RESEARCH_HOURS_KEY:
                self.get_cost_label("", self.RESEARCH_HOURS_KEY),
            self.ACQUISITION_HOURS_KEY:
                self.get_floattext(0, self.ACQUISITION_HOURS_KEY),
            self.ACQUISITION_COSTS_KEY:
                self.get_cost_label("", self.ACQUISITION_COSTS_KEY),
            self.ADMINISTRATION_HOURS_KEY:
                self.get_cost_label("", self.ADMINISTRATION_HOURS_KEY),
            self.ADMINISTRATION_COSTS_KEY:
                self.get_cost_label("", self.ADMINISTRATION_COSTS_KEY),
            self.PUBLIC_FUNDS_KEY:
                self.get_cost_label("", self.PUBLIC_FUNDS_KEY)
        }

        self.input_widgets[self.HOURLY_RATE_KEY].observe(
            lambda change: self.handle_int_update(change), names="value")

        self.reset_input_widgets()

        self.add_button = widgets.Button(
            description=_("Add"),
            button_style="success",
            layout=widgets.Layout(width=self.column_widths[self.ACTIONS]))
        self.add_button.on_click(lambda b: self.add_row())

        self.sort_buttons = {}
        self.filter_widgets = {}
        self.annual_working_hours_labels = {}
        self.research_hours_labels = {}
        self.acquisition_cost_labels = {}
        self.administration_hours_labels = {}
        self.administration_cost_labels = {}
        self.public_funds_labels = {}

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

        self.visualization = Visualization()
        self.visualization_output = widgets.Output()

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
            value=str(value),
            options=self.calculations.known_hourly_rates,
            ensure_option=False,
            layout=widgets.Layout(
                width=self.column_widths[self.HOURLY_RATE_KEY]))

    def get_float_slider(self, value, width_key):
        return widgets.FloatSlider(
            min=0, max=100, step=1, readout_format=".0f", value=value,
            layout=widgets.Layout(width=self.column_widths[width_key]))

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

    def compute_public_funds(self, row):
        return self.calculations.get_public_funds(
            self.compute_acquisition_costs(row),
            self.compute_administration_costs(row))

    def update_annual_working_hours_label(self, idx):
        if idx not in self.annual_working_hours_labels:
            return

        row = self.df.loc[idx]
        value = row[self.ANNUAL_WORKING_HOURS_KEY]
        self.annual_working_hours_labels[idx].value = (f"{value:.2f}")

    def update_research_hours_label(self, idx):
        if idx not in self.research_hours_labels:
            return

        row = self.df.loc[idx]
        value = row[self.RESEARCH_HOURS_KEY]
        self.research_hours_labels[idx].value = (f"{value:.2f}")

    def update_acquisition_costs_label(self, idx):
        if idx not in self.acquisition_cost_labels:
            return

        row = self.df.loc[idx]
        value = self.compute_acquisition_costs(row)
        self.acquisition_cost_labels[idx].value = f"{value:,.2f}"
        self.update_total_acquisition_costs()

    def update_administration_hours_label(self, idx):
        if idx not in self.administration_hours_labels:
            return

        row = self.df.loc[idx]
        value = row[self.ADMINISTRATION_HOURS_KEY]
        self.administration_hours_labels[idx].value = (f"{value:.2f}")

    def update_administration_costs_label(self, idx):
        if idx not in self.administration_cost_labels:
            return

        row = self.df.loc[idx]
        value = self.compute_administration_costs(row)
        self.administration_cost_labels[idx].value = f"{value:,.2f}"
        self.update_total_administration_costs()

    def update_public_funds_label(self, idx):
        if idx not in self.public_funds_labels:
            return

        row = self.df.loc[idx]
        value = self.compute_public_funds(row)
        self.public_funds_labels[idx].value = f"{value:,.2f}"

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

    # adds a new row to the DataFrame df
    def add_row(self):
        try:
            new_row = {}

            for col in self.COLUMNS.keys():

                # plain value from input row
                val = self.input_widgets[col].value

                # customize or calculate values wher necessary
                # DANGER:
                # We use values from new_row in the following if statements.
                # This simplification only works as long as columns only depend
                # on values in previous (left) colums!
                if col == self.ROLE_KEY:
                    # add untranslated role into dataframe
                    val = self.REVERSED_ROLES.get(val, val)

                elif col == self.HOURLY_RATE_KEY:
                    val = self.calculations.get_int(val)

                elif col == self.ANNUAL_WORKING_HOURS_KEY:
                    val = self.calculations.get_annual_working_hours(
                        new_row[self.EMPLOYMENT_PERCENTAGE_KEY])

                elif col == self.RESEARCH_HOURS_KEY:
                    val = self.calculations.get_research_hours(
                        new_row[self.ANNUAL_WORKING_HOURS_KEY],
                        new_row[self.RESEARCH_PERCENTAGE_KEY])

                elif col == self.ACQUISITION_COSTS_KEY:
                    val = self.calculations.get_costs(
                        new_row[self.HOURLY_RATE_KEY],
                        new_row[self.ACQUISITION_HOURS_KEY])

                elif col == self.ADMINISTRATION_HOURS_KEY:
                    employment_percentage = self.input_widgets[
                        self.EMPLOYMENT_PERCENTAGE_KEY].value
                    val = self.calculations.get_administration_hours(
                        employment_percentage)

                elif col == self.ADMINISTRATION_COSTS_KEY:
                    val = self.calculations.get_costs(
                        new_row[self.HOURLY_RATE_KEY],
                        new_row[self.ADMINISTRATION_HOURS_KEY])

                elif col == self.PUBLIC_FUNDS_KEY:
                    val = self.calculations.get_public_funds(
                        new_row[self.ACQUISITION_COSTS_KEY],
                        new_row[self.ADMINISTRATION_COSTS_KEY])

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
                             self.ANNUAL_WORKING_HOURS_KEY,
                             self.RESEARCH_HOURS_KEY,
                             self.ADMINISTRATION_HOURS_KEY):
                    # convert to numeric value before sorting
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

                elif col == self.PUBLIC_FUNDS_KEY:
                    funds = temp.apply(
                        self.compute_public_funds, axis=1
                    )
                    temp = temp.loc[funds.sort_values(ascending=asc).index]

                else:
                    temp = temp.sort_values(col, ascending=asc)

        return temp

    def delete_row(self, idx):
        self.df = self.df.drop(index=idx)
        self.refresh_table()

    def handle_int_update(self, change):
        try:
            # if there is any text
            # it must be possible to convert to int
            if change["new"]:
                int(change["new"])
        except ValueError:
            # if the new value can't be converted to int
            # revert the change
            change.owner.value = change.old

    def handle_role_update(self, idx, col, new_value):
        self.df.at[idx, col] = self.REVERSED_ROLES.get(new_value, new_value)

    def handle_hourly_rate_update(self, idx, change):

        value = None
        try:
            # if there is any text
            # it must be possible to convert to int
            if change["new"]:
                value = int(change["new"])
        except ValueError:
            # if the new value can't be converted to int
            # revert the change
            change.owner.value = change.old
            value = change.old

        new_hourly_rate = value if value else 0
        self.df.at[idx, self.HOURLY_RATE_KEY] = new_hourly_rate

        # update dependencies
        self.update_acquisition_costs(idx)
        self.update_administration_costs(idx)
        self.update_public_funds(idx)

    def handle_employment_percentage_update(self, idx, new_value):

        self.df.at[idx, self.EMPLOYMENT_PERCENTAGE_KEY] = new_value

        # update annual working hours
        annual_working_hours = (
            self.calculations.get_annual_working_hours(new_value))
        self.df.at[idx, self.ANNUAL_WORKING_HOURS_KEY] = annual_working_hours
        self.update_annual_working_hours_label(idx)

        # update research hours
        research_percentage = float(
            self.df.at[idx, self.RESEARCH_PERCENTAGE_KEY])
        research_hours = self.calculations.get_research_hours(
            annual_working_hours, research_percentage)
        self.df.at[idx, self.RESEARCH_HOURS_KEY] = research_hours
        self.update_research_hours_label(idx)

        # update administration hours
        administration_hours = (
            self.calculations.get_administration_hours(new_value))
        self.df.at[idx, self.ADMINISTRATION_HOURS_KEY] = administration_hours
        self.update_administration_hours_label(idx)

        # update administration cost
        self.update_administration_costs(idx)

        # update public funds
        public_funds = self.calculations.get_public_funds(
            self.df.at[idx, self.ACQUISITION_COSTS_KEY],
            self.df.at[idx, self.ADMINISTRATION_COSTS_KEY])
        self.df.at[idx, self.PUBLIC_FUNDS_KEY] = public_funds
        self.update_public_funds_label(idx)

    def handle_research_percentage_update(self, idx, new_value):

        self.df.at[idx, self.RESEARCH_PERCENTAGE_KEY] = new_value

        # update research hours
        annual_working_hours = self.df.at[idx, self.ANNUAL_WORKING_HOURS_KEY]
        research_hours = self.calculations.get_research_hours(
            annual_working_hours, new_value)
        self.df.at[idx, self.RESEARCH_HOURS_KEY] = research_hours
        self.update_research_hours_label(idx)

    def handle_acquisition_hours_update(self, idx, new_value):
        self.df.at[idx, self.ACQUISITION_HOURS_KEY] = new_value
        self.update_acquisition_costs(idx)
        self.update_public_funds(idx)

    def update_acquisition_costs(self, idx):
        acquisition_costs = self.calculations.get_costs(
            self.df.at[idx, self.HOURLY_RATE_KEY],
            self.df.at[idx, self.ACQUISITION_HOURS_KEY])
        self.df.at[idx, self.ACQUISITION_COSTS_KEY] = acquisition_costs
        self.update_acquisition_costs_label(idx)

    def update_administration_costs(self, idx):
        administration_costs = self.calculations.get_costs(
            self.df.at[idx, self.HOURLY_RATE_KEY],
            self.df.at[idx, self.ADMINISTRATION_HOURS_KEY])
        self.df.at[idx, self.ADMINISTRATION_COSTS_KEY] = administration_costs
        self.update_administration_costs_label(idx)

    def update_public_funds(self, idx):
        public_funds = self.calculations.get_public_funds(
            self.df.at[idx, self.ACQUISITION_COSTS_KEY],
            self.df.at[idx, self.ADMINISTRATION_COSTS_KEY])
        self.df.at[idx, self.PUBLIC_FUNDS_KEY] = public_funds
        self.update_public_funds_label(idx)

    def handle_cell_update(self, idx, col, change):
        try:
            new_value = change["new"]

            if col == self.NAME_KEY:
                self.df.at[idx, col] = new_value
                self.refresh_visualization()

            elif col == self.ROLE_KEY:
                self.handle_role_update(idx, col, new_value)

            elif col == self.HOURLY_RATE_KEY:
                self.handle_hourly_rate_update(idx, change)
                self.refresh_visualization()

            elif col == self.EMPLOYMENT_PERCENTAGE_KEY:
                self.handle_employment_percentage_update(idx, new_value)
                self.refresh_visualization()

            elif col == self.RESEARCH_PERCENTAGE_KEY:
                self.handle_research_percentage_update(idx, new_value)

            elif col == self.ACQUISITION_HOURS_KEY:
                self.handle_acquisition_hours_update(idx, new_value)
                self.refresh_visualization()

        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def get_cell_annual_working_hours(self, idx, row):
        value = self.calculations.get_annual_working_hours(
            row[self.EMPLOYMENT_PERCENTAGE_KEY])
        cell = self.get_cost_label(
            f"{value:.2f}", self.ANNUAL_WORKING_HOURS_KEY)
        self.annual_working_hours_labels[idx] = cell
        return cell

    def get_cell_research_hours(self, idx, row):
        try:
            annual_working_hours = float(row[self.ANNUAL_WORKING_HOURS_KEY])
        except Exception:
            annual_working_hours = 0.0
        research_percentage = row[self.RESEARCH_PERCENTAGE_KEY]
        value = self.calculations.get_research_hours(
            annual_working_hours, research_percentage)
        cell = self.get_cost_label(f"{value:.2f}", self.RESEARCH_HOURS_KEY)
        self.research_hours_labels[idx] = cell
        return cell

    def get_cell_acquisistion_costs(self, idx, row):
        value = self.compute_acquisition_costs(row)
        cell = self.get_cost_label(f"{value:,.2f}", self.ACQUISITION_COSTS_KEY)
        self.acquisition_cost_labels[idx] = cell
        return cell

    def get_cell_administration_hours(self, idx, row):
        try:
            value = float(row[self.ADMINISTRATION_HOURS_KEY])
            text = f"{value:.2f}"
        except Exception:
            text = "0.00"
        cell = self.get_cost_label(text, self.ADMINISTRATION_HOURS_KEY)
        self.administration_hours_labels[idx] = cell
        return cell

    def get_cell_administration_costs(self, idx, row):
        value = self.compute_administration_costs(row)
        cell = self.get_cost_label(
            f"{value:,.2f}", self.ADMINISTRATION_COSTS_KEY)
        self.administration_cost_labels[idx] = cell
        return cell

    def get_cell_public_funds(self, idx, row):
        value = self.compute_public_funds(row)
        cell = self.get_cost_label(f"{value:,.2f}", self.PUBLIC_FUNDS_KEY)
        self.public_funds_labels[idx] = cell
        return cell

    def get_cell(self, idx, row, col):

        observing = True

        if col == self.NAME_KEY:
            cell = self.get_name_text(row[col])

        elif col == self.ROLE_KEY:
            cell = self.get_role_dropdown(self.ROLES[row[col]])

        elif col == self.HOURLY_RATE_KEY:
            cell = self.get_hourly_rate_combobox(row[col])

        elif col == self.EMPLOYMENT_PERCENTAGE_KEY:
            cell = self.get_float_slider(
                row[col], self.EMPLOYMENT_PERCENTAGE_KEY)

        elif col == self.ANNUAL_WORKING_HOURS_KEY:
            cell = self.get_cell_annual_working_hours(idx, row)
            observing = False

        elif col == self.RESEARCH_PERCENTAGE_KEY:
            cell = self.get_float_slider(
                row[col], self.RESEARCH_PERCENTAGE_KEY)

        elif col == self.RESEARCH_HOURS_KEY:
            cell = self.get_cell_research_hours(idx, row)
            observing = False

        elif col == self.ACQUISITION_HOURS_KEY:
            cell = self.get_floattext(row[col], self.ACQUISITION_HOURS_KEY)

        elif col == self.ACQUISITION_COSTS_KEY:
            cell = self.get_cell_acquisistion_costs(idx, row)
            observing = False

        elif col == self.ADMINISTRATION_HOURS_KEY:
            cell = self.get_cell_administration_hours(idx, row)
            observing = False

        elif col == self.ADMINISTRATION_COSTS_KEY:
            cell = self.get_cell_administration_costs(idx, row)
            observing = False

        elif col == self.PUBLIC_FUNDS_KEY:
            cell = self.get_cell_public_funds(idx, row)
            observing = False

        else:
            print("Warning: unhandled col", col)

        if observing:
            cell.observe(
                lambda change, i=idx, c=col:
                    self.handle_cell_update(i, c, change), names="value")

        return cell

    def refresh_table(self):

        self.annual_working_hours_labels.clear()
        self.research_hours_labels.clear()
        self.acquisition_cost_labels.clear()
        self.administration_hours_labels.clear()
        self.administration_cost_labels.clear()
        self.public_funds_labels.clear()

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
            # button_style="danger" seems to be too red...
            # description="X🗑️❌✖✕ⓧ⊗⨯",
            btn = widgets.Button(
                description="✖",
                layout=widgets.Layout(width=self.column_widths[self.ACTIONS]))
            btn.on_click(lambda b, i=idx: self.delete_row(i))
            btn.style.button_color = "#C76A2A"
            btn.style.text_color = "white"

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

        self.refresh_visualization()

    def refresh_visualization(self):
        with self.visualization_output:
            self.visualization.show(self)

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
            .jp-OutputArea .widget-readout {
                width: 30px !important;
                min-width: 30px !important;
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
            self.output,
            self.visualization_output])
        container.layout.padding = "0px"

        # --- display program ---
        display(container)
        self.refresh_table()
