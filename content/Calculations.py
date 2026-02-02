class Calculations:

    def __init__(self) -> None:
        self.ANNUAL_WORKING_HOURS = 1940  # hours
        self.ADMINISTRATION_FACTOR = 0.02
        self.known_hourly_rates = ["55", "69", "87", "89", "103", "117"]

    def get_annual_working_hours(self, employment_percentage):
        return self._get_percentage(
            self.ANNUAL_WORKING_HOURS, employment_percentage)

    def get_research_hours(self, annual_working_hours, research_percentage):
        return self._get_percentage(
            annual_working_hours, research_percentage)

    def get_administration_hours(self, employment_percentage):
        return (self.get_annual_working_hours(employment_percentage) *
                self.ADMINISTRATION_FACTOR)

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

    def get_public_funds(self, acquisition_costs, administration_costs):
        return (self.get_float(acquisition_costs) +
                self.get_float(administration_costs))

    def get_remaining_budget(
            self, total_budget, acquisition_expenses, administrative_expenses):
        return total_budget - acquisition_expenses - administrative_expenses

    def _get_percentage(self, value, percentage):
        return value * percentage / 100
