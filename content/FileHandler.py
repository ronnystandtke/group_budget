from IPython.display import display, HTML, clear_output
import base64
import json
import traceback


class FileHandler:

    def __init__(self) -> None:
        # main keys for our JSON file
        self.TOTAL_BUDGET_KEY = "total_budget"
        self.EMPLOYEES_KEY = "employees"

    def load_data(self, content):
        try:
            return json.loads(bytes(content).decode('utf-8'))
        except Exception:
            print(traceback.format_exc())
            with self.output:
                print(traceback.format_exc())

    def save_data(self, total_budget, sorted_df, download_output):

        data_to_export = {
            self.TOTAL_BUDGET_KEY: total_budget,
            self.EMPLOYEES_KEY: sorted_df.to_dict(orient='records')
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

        with download_output:
            clear_output()
            display(HTML(html))
