from datetime import date
from IPython.display import display, HTML, clear_output
import base64
import json
import traceback


class FileHandler:

    def __init__(self) -> None:
        # main keys for our JSON file
        self.YEAR_KEY = "year"
        self.ANNUAL_WORKING_TIME_KEY = "annualWorkingTime"
        self.TOTAL_BUDGET_KEY = "totalBudget"
        self.MANAGEMENT_ALLOWANCE_KEY = "managementAllowance"
        self.ADMINISTRATION_PERCENTAGE_KEY = "administrationPercentage"
        self.EMPLOYEES_KEY = "employees"

    def load_data(self, content):
        try:
            data = json.loads(bytes(content).decode('utf-8'))
            return self._restore_dates(data)
        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def save_data(self, year, annual_working_time, total_budget,
                  management_allowance, administration_percentage, df,
                  download_output):

        try:

            data_to_export = {
                self.YEAR_KEY: year,
                self.ANNUAL_WORKING_TIME_KEY: annual_working_time,
                self.TOTAL_BUDGET_KEY: total_budget,
                self.MANAGEMENT_ALLOWANCE_KEY: management_allowance,
                self.ADMINISTRATION_PERCENTAGE_KEY: administration_percentage,
                self.EMPLOYEES_KEY: df.to_dict(orient='records')
            }

            json_str = json.dumps(
                data_to_export,
                indent=2,
                default=self._json_serializer
            )

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

            with download_output:
                clear_output()
                display(HTML(html))

        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def _json_serializer(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return obj

    def _restore_dates(self, obj):

        if isinstance(obj, dict):
            return {k: self._restore_dates(v) for k, v in obj.items()}

        elif isinstance(obj, list):
            return [self._restore_dates(i) for i in obj]

        elif isinstance(obj, str):
            try:
                return date.fromisoformat(obj)
            except Exception:
                return obj

        return obj
