class Calculations:

    def __init__(self) -> None:
        self.ANNUAL_WORKING_HOURS = 1940  # hours
        self.ADMINISTRATION_FACTOR = 0.02
        self.known_hourly_rates = ["55", "69", "87", "89", "103", "117"]

    def get_administration_hours(self, employment_percentage):
        return (
            self.ANNUAL_WORKING_HOURS *
            employment_percentage *
            self.ADMINISTRATION_FACTOR / 100
        )

    def get_costs(self, hourly_rate, hours):
        try:
            return hourly_rate * hours
        except Exception:
            return 0.0
