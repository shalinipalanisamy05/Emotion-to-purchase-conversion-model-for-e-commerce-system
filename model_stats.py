"""
model_stats.py — ML Model Performance Charts for ShopSmart
Call render_model_stats() from page_home() in app.py
"""

import streamlit as st
import plotly.graph_objects as go


def render_model_stats():
    """Render ML model performance charts inline on the home page."""

    GOLD   = "#f5c518"
    GREEN  = "#22c55e"
    RED    = "#ef4444"
    BLUE   = "#3b82f6"
    ORANGE = "#f97316"
    BG     = "#141414"
    CARD   = "#1a1a1a"
    TEXT   = "#ffffff"
    GRID   = "#2a2a2a"

    # margin removed from layout_base — set per chart to avoid conflicts
    layout_base = dict(
        paper_bgcolor=BG,
        plot_bgcolor=CARD,
        font=dict(color=TEXT, family="DM Sans"),
    )

    st.markdown("""
    <div class="section-header">
        <div class="section-title">📊 Model Performance</div>
        <div class="section-sub">Real metrics from training on 50,000 IMDB reviews</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Row 1: Accuracy gauges ────────────────────────────────────────────────
    g1, g2, g3, g4 = st.columns(4)

    gauge_style = dict(
        axis=dict(tickcolor=TEXT, tickwidth=1, ticklen=4,
                  range=[0, 100], tickvals=[0, 25, 50, 75, 100]),
        bar=dict(thickness=0.25),
        bgcolor=CARD,
        borderwidth=0,
        steps=[
            dict(range=[0,  50], color="#2a2a2a"),
            dict(range=[50, 75], color="#292929"),
            dict(range=[75,100], color="#222222"),
        ],
    )

    for col, (title, val, color) in zip(
        [g1, g2, g3, g4],
        [
            ("Sentiment\nAccuracy",   85, GREEN),
            ("Fake Review\nAccuracy", 96, BLUE),
            ("Genuine\nPrecision",    97, GOLD),
            ("Fake\nRecall",          81, ORANGE),
        ]
    ):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            number=dict(suffix="%", font=dict(size=28, color=color)),
            title=dict(text=title, font=dict(size=13, color=TEXT)),
            gauge={**gauge_style, "bar": dict(color=color, thickness=0.25)},
        ))
        fig.update_layout(**layout_base, height=200, margin=dict(t=40, b=10, l=20, r=20))
        col.plotly_chart(fig, use_container_width=True)

    # ── Row 2: Bar charts — precision / recall / F1 ───────────────────────────
    col_sent, col_fake = st.columns(2)
    metrics = ["Precision", "Recall", "F1-Score"]

    # Sentiment model
    with col_sent:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Negative", x=metrics, y=[0.84, 0.86, 0.85],
            marker_color=RED, text=["0.84", "0.86", "0.85"],
            textposition="outside", textfont=dict(color=TEXT, size=12),
        ))
        fig.add_trace(go.Bar(
            name="Positive", x=metrics, y=[0.85, 0.84, 0.85],
            marker_color=GREEN, text=["0.85", "0.84", "0.85"],
            textposition="outside", textfont=dict(color=TEXT, size=12),
        ))
        fig.update_layout(
            **layout_base,
            title=dict(text="🤖 Sentiment Model  (TF-IDF + Naive Bayes)", font=dict(size=14, color=GOLD)),
            barmode="group", height=320,
            margin=dict(t=50, b=40, l=40, r=20),
            yaxis=dict(range=[0.70, 0.96], gridcolor=GRID, tickformat=".0%",
                       tickvals=[0.70, 0.75, 0.80, 0.85, 0.90, 0.95]),
            legend=dict(bgcolor=BG, bordercolor="#333", borderwidth=1),
            xaxis=dict(gridcolor=GRID),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Fake review model
    with col_fake:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Genuine", x=metrics, y=[0.97, 0.99, 0.98],
            marker_color=BLUE, text=["0.97", "0.99", "0.98"],
            textposition="outside", textfont=dict(color=TEXT, size=12),
        ))
        fig.add_trace(go.Bar(
            name="Fake", x=metrics, y=[0.90, 0.81, 0.85],
            marker_color=ORANGE, text=["0.90", "0.81", "0.85"],
            textposition="outside", textfont=dict(color=TEXT, size=12),
        ))
        fig.update_layout(
            **layout_base,
            title=dict(text="🔍 Fake Review Model  (Random Forest)", font=dict(size=14, color=GOLD)),
            barmode="group", height=320,
            margin=dict(t=50, b=40, l=40, r=20),
            yaxis=dict(range=[0.65, 1.07], gridcolor=GRID, tickformat=".0%",
                       tickvals=[0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]),
            legend=dict(bgcolor=BG, bordercolor="#333", borderwidth=1),
            xaxis=dict(gridcolor=GRID),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Row 3: Dataset donuts + confusion matrices ────────────────────────────
    col_d1, col_d2, col_cm1, col_cm2 = st.columns(4)

    # Sentiment dataset donut
    with col_d1:
        fig = go.Figure(go.Pie(
            labels=["Positive", "Negative"], values=[25000, 25000],
            hole=0.6, marker_colors=[GREEN, RED],
            textinfo="label+percent", textfont=dict(size=11, color=TEXT),
            hovertemplate="%{label}: %{value:,}<extra></extra>",
        ))
        fig.add_annotation(text="50K", x=0.5, y=0.5,
                           font=dict(size=20, color=TEXT, family="Playfair Display"),
                           showarrow=False)
        fig.update_layout(**layout_base, height=260,
                          title=dict(text="Sentiment Dataset", font=dict(size=13, color=GOLD)),
                          showlegend=False, margin=dict(t=45, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    # Fake review dataset donut
    with col_d2:
        fig = go.Figure(go.Pie(
            labels=["Genuine", "Fake"], values=[2626, 374],
            hole=0.6, marker_colors=[BLUE, ORANGE],
            textinfo="label+percent", textfont=dict(size=11, color=TEXT),
            hovertemplate="%{label}: %{value:,}<extra></extra>",
        ))
        fig.add_annotation(text="3K", x=0.5, y=0.5,
                           font=dict(size=20, color=TEXT, family="Playfair Display"),
                           showarrow=False)
        fig.update_layout(**layout_base, height=260,
                          title=dict(text="Fake Review Dataset", font=dict(size=13, color=GOLD)),
                          showlegend=False, margin=dict(t=45, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    # Confusion matrix — Sentiment
    with col_cm1:
        z = [[258, 42], [48, 252]]
        fig = go.Figure(go.Heatmap(
            z=z, x=["Pred Neg", "Pred Pos"], y=["True Neg", "True Pos"],
            colorscale=[[0, "#1a1a2e"], [1, "#22c55e"]],
            text=[[str(v) for v in row] for row in z],
            texttemplate="%{text}", textfont=dict(size=16, color=TEXT),
            showscale=False,
        ))
        fig.update_layout(**layout_base, height=260,
                          title=dict(text="Sentiment Confusion Matrix", font=dict(size=13, color=GOLD)),
                          margin=dict(t=45, b=10, l=60, r=10))
        st.plotly_chart(fig, use_container_width=True)

    # Confusion matrix — Fake Review
    with col_cm2:
        z = [[520, 5], [14, 61]]
        fig = go.Figure(go.Heatmap(
            z=z, x=["Pred Gen", "Pred Fake"], y=["True Gen", "True Fake"],
            colorscale=[[0, "#1a1a2e"], [1, "#f97316"]],
            text=[[str(v) for v in row] for row in z],
            texttemplate="%{text}", textfont=dict(size=16, color=TEXT),
            showscale=False,
        ))
        fig.update_layout(**layout_base, height=260,
                          title=dict(text="Fake Review Confusion Matrix", font=dict(size=13, color=GOLD)),
                          margin=dict(t=45, b=10, l=70, r=10))
        st.plotly_chart(fig, use_container_width=True)