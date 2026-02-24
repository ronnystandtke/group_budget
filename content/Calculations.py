class Calculations:

    def __init__(self) -> None:
        self.DEFAULT_ANNUAL_WORKING_HOURS = 2120
        self.DEFAULT_ADMINISTRATION_PERCENTAGE = 2
        self.ANNUAL_WORKING_HOURS = 1940
        self.known_hourly_rates = ["55", "69", "87", "89", "103", "117"]

    def get_management_share(self, management_allowance,
                             df, management_key, row):
        managers = df[df.get(management_key, False).fillna(False)]

        if len(managers) == 0:
            return 0.0

        if not row[management_key]:
            return 0.0

        return management_allowance / len(managers)

    def get_annual_working_hours(self, employment_percentage):
        return self._get_percentage(
            self.ANNUAL_WORKING_HOURS, employment_percentage)

    def get_research_hours(self, annual_working_hours, research_percentage):
        return self._get_percentage(
            annual_working_hours, research_percentage)

    def get_administration_hours(
            self, is_management, employment_percentage, administration_factor):
        if is_management:
            return 0
        else:
            return (self.get_annual_working_hours(employment_percentage) *
                    administration_factor / 100)

    def get_float(self, value):
        try:
            return float(value)
        except Exception:
            return 0.0

    def get_int(self, value):
        try:
            return int(value)
        except Exception:
            return 0

    def get_costs(self, hourly_rate, hours):
        return self.get_float(hourly_rate) * self.get_float(hours)

    def get_public_funds(self, acquisition_costs,
                         management_costs, administration_costs):
        return (self.get_float(acquisition_costs) +
                self.get_float(management_costs) +
                self.get_float(administration_costs))

    def get_remaining_budget(
            self, total_budget, acquisition_expenses,
            management_expenses, administrative_expenses):
        return (total_budget - acquisition_expenses -
                management_expenses - administrative_expenses)

    def _get_percentage(self, value, percentage):
        return value * percentage / 100
