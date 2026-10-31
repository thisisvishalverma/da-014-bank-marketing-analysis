# Faculty demonstration guide (3–5 minutes)

1. From the repository folder, start the dashboard with `streamlit run app.py` and open the local browser link.
2. On **Overview**, explain that response rate is `yes` subscriptions divided by valid target records in the current filtered selection.
3. Change a sidebar filter such as `contact` or `job`; show how KPI values and charts update. Restore all values afterward.
4. Change **Compare response rate by segment** to education or month. Hover over bars to show the record and response counts behind each rate.
5. Point out the contact-frequency chart and channel, month, and weekday comparisons. `campaign` counts the contacts during the current campaign, including the last contact.
6. Open **Findings & recommendations**. Explain the 30-record minimum group size and that historical associations are descriptive, not causal.
7. Open **Data & methodology** to show the target definition, cleaning notes, limitation of `duration`, and UCI source.
8. Expand **Preview filtered records** to show that the dashboard uses the underlying data rows.

Suggested closing: “This prototype is an exploratory analysis. Any campaign change based on these historical associations should be tested on a comparable audience before rollout.”
