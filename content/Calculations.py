class Calculations:

    def __init__(self) -> None:
        # e.g. here:
        # https://www.pa.fin.be.ch/de/start/themen/anstellungsbedingungen/arbeitszeit-und-ferien/sollarbeitszeittabellen.html
        self.DEFAULT_ANNUAL_WORKING_HOURS = 2120
        self.DEFAULT_ADMINISTRATION_PERCENTAGE = 2
        self.HOURS_PER_DAY = 8.4
        self.known_hourly_rates = ["55", "69", "87", "89", "103", "117"]

    def get_management_share(self, management_allowance,
                             df, management_key, row):
        managers = df[df.get(management_key, False).fillna(False)]

        if len(managers) == 0:
            return 0.0

        if not row[management_key]:
            return 0.0

        return management_allowance / len(managers)

    def get_annual_working_hours(self, annual_working_hours,
                                 employment_percentage, vacation_days):
        working_hours = (
            annual_working_hours - (vacation_days * self.HOURS_PER_DAY))
        return self._get_percentage(working_hours, employment_percentage)

    def get_annual_vacation_hours(self, vacation_days, employment_percentage):
        return self._get_percentage(
            vacation_days * self.HOURS_PER_DAY, employment_percentage)

    def get_research_hours(self, annual_working_hours, research_percentage):
        return self._get_percentage(
            annual_working_hours, research_percentage)

    def get_administration_hours(self, is_management, annual_working_hours,
                                 administration_factor):
        if is_management:
            return 0
        else:
            return annual_working_hours * administration_factor / 100

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

    def get_vacation_costs(self, is_ilv, hourly_rate, hours):
        if is_ilv:
            return 0
        else:
            return self.get_float(hourly_rate) * self.get_float(hours)

    def get_costs(self, hourly_rate, hours):
        return self.get_float(hourly_rate) * self.get_float(hours)

    def get_public_funds(self, vacation_costs, acquisition_costs,
                         management_costs, administration_costs):
        return (self.get_float(vacation_costs) +
                self.get_float(acquisition_costs) +
                self.get_float(management_costs) +
                self.get_float(administration_costs))

    def get_remaining_budget(
            self, total_budget, vacation_expenses, acquisition_expenses,
            management_expenses, administrative_expenses):
        return (total_budget - vacation_expenses - acquisition_expenses -
                management_expenses - administrative_expenses)

    def get_vacation_days(self, birthdate, year):
        if not birthdate:
            return 0

        age = year - birthdate.year

        if age <= 20:
            return 28
        elif age <= 44:
            return 25
        elif age <= 55:
            return 28
        else:
            return 33

    def _get_percentage(self, value, percentage):
        return value * percentage / 100
