import plotly.graph_objects as go
from IPython.display import clear_output, display, HTML
import gettext

gettext.bindtextdomain('finances', 'translations')
gettext.textdomain('finances')

_ = gettext.gettext


class Visualization:

    def show(self, finances):

        budget = finances.total_budget.value
        total_spent = finances.df[finances.PUBLIC_FUNDS_KEY].sum()
        remaining_budget = max(0, budget - total_spent)
        utilization_percentage = (
            (total_spent / budget) * 100 if budget > 0 else 0)

        # create sorted list of employees names (big spenders first)
        sorted_df = finances.df.sort_values(
            finances.PUBLIC_FUNDS_KEY, ascending=False)
        sorted_names = sorted_df[finances.NAME_KEY].tolist()

        # --- nodes and positioning ---
        all_labels = (
            [_("Total Budget"), _("Personnel Costs"), _("Acquisition"),
             _("Administration"), _("Remaining")] + sorted_names)
        label_map = {name: i for i, name in enumerate(all_labels)}

        # --- links ---
        sources, targets, values, = [], [], []

        # total budget splitting
        sources.extend(
            [label_map[_("Total Budget")], label_map[_("Total Budget")]])
        targets.extend(
            [label_map[_("Personnel Costs")], label_map[_("Remaining")]])
        values.extend([total_spent, remaining_budget])

        # personnel cost splitting
        sources.extend(
            [label_map[_("Personnel Costs")], label_map[_("Personnel Costs")]])
        targets.extend(
            [label_map[_("Acquisition")], label_map[_("Administration")]])
        values.extend(
            [finances.df[finances.ACQUISITION_COSTS_KEY].sum(),
             finances.df[finances.ADMINISTRATION_COSTS_KEY].sum()])

        # # acquisition and administration cost splitting
        name_df = finances.df.set_index(finances.NAME_KEY)
        for name in sorted_names:
            acquisition_costs = name_df.loc[
                name, finances.ACQUISITION_COSTS_KEY]
            administration_costs = name_df.loc[
                name, finances.ADMINISTRATION_COSTS_KEY]

            if acquisition_costs > 0:
                sources.append(label_map[_("Acquisition")])
                targets.append(label_map[name])
                values.append(acquisition_costs)

            if administration_costs > 0:
                sources.append(label_map[_("Administration")])
                targets.append(label_map[name])
                values.append(administration_costs)

        # --- plot ---

        # custom colors
        employee_color = "#D8E4E8"

        node_colors = [
            "#C76A2A",  # Total Budget
            "#D89A5A",  # Personnel Costs
            "#9DB7C9",  # Acquisition
            "#B7CEDA",  # Administration
            "#9DBFA6",  # Remaining
        ]

        node_colors.extend([employee_color] * len(sorted_names))

        def with_alpha(hex_color, alpha=0.45):
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"rgba({r},{g},{b},{alpha})"

        link_colors = [with_alpha(node_colors[src]) for src in sources]

        fig = go.Figure(data=[go.Sankey(
            arrangement="fixed",
            node=dict(
                label=all_labels,
                color=node_colors,
                pad=16,
                thickness=15,
                hovertemplate='%{label}<br>CHF %{value:,.2f}<extra></extra>'
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors,
                hovertemplate=(
                    '%{source.label} → %{target.label}<br>'
                    'CHF %{value:,.2f}<extra></extra>'
                    )
            )
        )])

        title_str = (
            "<b>" + _("Budget Flow Analysis") + "</b><br>" +
            _("Utilization: {utilization_percentage:.1f}% |"
              " Budget: {budget:,.2f} CHF").format(
                  utilization_percentage=utilization_percentage, budget=budget)
        )
        fig.update_layout(
            title_text=title_str,
            height=900, font_size=11,
            margin=dict(t=100, b=100, l=0, r=0)
        )

        clear_output(wait=True)
        display(HTML(fig.to_html(include_plotlyjs='cdn')))
