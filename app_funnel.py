import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Заголовок приложения
st.set_page_config(page_title="Воронка продаж", layout="wide")
st.title("📊 Анализ воронки продаж")
st.markdown("---")


# Функция для загрузки и обработки данных
@st.cache_data
def load_data(uploaded_file):
    # Чтение Excel файла
    df = pd.read_excel(uploaded_file, header=None)

    # Установка правильных заголовков
    # Первые 2 строки - это заголовки
    df.columns = range(df.shape[1])

    # Создание мультииндекса для столбцов
    new_columns = []
    for i in range(df.shape[1]):
        if i == 0:
            new_columns.append(('Дата', ''))
        elif i == 1:
            new_columns.append(('Филиал', ''))
        else:
            # Определяем этап воронки
            stage_idx = (i - 2) // 2
            stages = ['Холодный', 'Встреча', 'КП', 'Согласование', 'Договор', 'Поставка']
            stage = stages[stage_idx] if stage_idx < len(stages) else f'Этап_{stage_idx}'

            # Определяем тип данных (Кол-во или Тонн)
            data_type = 'Кол-во' if (i - 2) % 2 == 0 else 'Тонн'

            new_columns.append((stage, data_type))

    # Применяем мультииндекс
    df.columns = pd.MultiIndex.from_tuples(new_columns)

    # Удаляем первые две строки (старые заголовки)
    df = df.iloc[2:].reset_index(drop=True)

    # Преобразуем даты
    df[('Дата', '')] = pd.to_datetime(df[('Дата', '')])

    # Преобразуем числовые столбцы
    for col in df.columns:
        if col[1] in ['Кол-во', 'Тонн']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Заполняем NaN нулями
    for col in df.columns:
        if col[1] in ['Кол-во', 'Тонн']:
            df[col] = df[col].fillna(0)

    return df


# Сайдбар для фильтров
with st.sidebar:
    st.header("⚙️ Настройки фильтров")

    # Загрузка файла
    uploaded_file = st.file_uploader("Загрузите файл Excel", type=['xlsx'])

    if uploaded_file is None:
        st.warning("⚠️ Пожалуйста, загрузите файл Excel для анализа")
        st.info("Формат файла должен соответствовать предоставленной таблице")
        st.stop()

    try:
        df = load_data(uploaded_file)
        st.success(f"✅ Файл успешно загружен! Записей: {len(df)}")

        # Информация о данных
        with st.expander("📊 Информация о данных"):
            st.write(f"**Диапазон дат:** {df[('Дата', '')].min().date()} - {df[('Дата', '')].max().date()}")
            st.write(f"**Филиалы:** {', '.join(df[('Филиал', '')].unique())}")
            st.write(f"**Этапы воронки:** Холодный, Встреча, КП, Согласование, Договор, Поставка")

    except Exception as e:
        st.error(f"❌ Ошибка при загрузке файла: {str(e)}")
        st.stop()

    # Выбор метрики
    metric = st.radio(
        "Выберите метрику для анализа:",
        ['Кол-во', 'Тонн'],
        index=0,
        help="Анализировать по количеству сделок или по тоннажу"
    )

    # Выбор периода
    period_option = st.radio(
        "Выберите период:",
        ['За весь период', 'Конкретная дата'],
        index=1
    )

    if period_option == 'Конкретная дата':
        available_dates = sorted(df[('Дата', '')].dt.date.unique())
        selected_date = st.selectbox(
            "Выберите дату:",
            available_dates,
            format_func=lambda x: x.strftime('%Y-%m-%d'),
            help="Выберите дату для анализа воронки"
        )
        selected_date_dt = pd.to_datetime(selected_date)
        period_label = selected_date
    else:
        selected_date = "За весь период"
        selected_date_dt = None
        period_label = f"Весь период ({df[('Дата', '')].min().date()} - {df[('Дата', '')].max().date()})"

    # Выбор филиала
    available_branches = sorted(df[('Филиал', '')].unique())
    selected_branch = st.selectbox(
        "Выберите филиал:",
        ['Все филиалы'] + list(available_branches),
        help="Анализировать один филиал или все вместе"
    )

    # Настройки визуализации
    st.header("🎨 Настройки графика")
    show_values = st.checkbox("Показывать значения на графике", value=True)
    show_percentage = st.checkbox("Показывать процент от предыдущего этапа", value=True)

    # Выбор ориентации воронки
    funnel_orientation = st.radio(
        "Ориентация воронки:",
        ['Вертикальная', 'Горизонтальная'],
        index=0
    )

    # Выбор цвета для воронки
    color_options = {
        'Синяя гамма': ['#1f77b4', '#aec7e8', '#6baed6', '#3182bd', '#08519c', '#08306b'],
        'Красная гамма': ['#ef6548', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26', '#a50f15'],
        'Зеленая гамма': ['#31a354', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#005a32'],
        'Фиолетовая гамма': ['#756bb1', '#bcbddc', '#9e9ac8', '#807dba', '#6a51a3', '#4a1486'],
        'Оранжевая гамма': ['#fd8d3c', '#fdbe85', '#fdae6b', '#fd8d3c', '#f16913', '#d94801'],
        'Серая гамма': ['#636363', '#bdbdbd', '#969696', '#737373', '#525252', '#252525']
    }

    selected_color = st.selectbox(
        "Цветовая схема:",
        list(color_options.keys()),
        index=0
    )

    # Дополнительные настройки
    st.header("📈 Дополнительные опции")
    show_table = st.checkbox("Показать исходные данные", value=False)
    normalize_values = st.checkbox("Нормализовать значения (для сравнения)", value=False)

# Основная область
if uploaded_file is not None and df is not None:
    # Получаем этапы воронки из данных
    stages = []
    for col in df.columns:
        if col[0] not in ['Дата', 'Филиал'] and col[1] == metric and col[0] not in stages:
            stages.append(col[0])

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"📊 Воронка продаж - {metric}")

        # Подготовка данных для воронки
        if period_option == 'За весь период':
            # Агрегируем данные за весь период
            if selected_branch != 'Все филиалы':
                filtered_by_branch = df[df[('Филиал', '')] == selected_branch]
                values = []
                for stage in stages:
                    total = filtered_by_branch[(stage, metric)].sum()
                    values.append(float(total))

                funnel_data = pd.DataFrame({
                    'Этап': stages,
                    'Значение': values
                })
            else:
                # Все филиалы за весь период
                values = []
                for stage in stages:
                    total = df[(stage, metric)].sum()
                    values.append(float(total))

                funnel_data = pd.DataFrame({
                    'Этап': stages,
                    'Значение': values
                })
        else:
            # Конкретная дата
            if selected_branch != 'Все филиалы':
                filtered_data = df[(df[('Дата', '')] == selected_date_dt) &
                                   (df[('Филиал', '')] == selected_branch)]

                if not filtered_data.empty:
                    values = []
                    for stage in stages:
                        value = filtered_data.iloc[0][(stage, metric)]
                        values.append(float(value))

                    funnel_data = pd.DataFrame({
                        'Этап': stages,
                        'Значение': values
                    })
                else:
                    st.warning(f"Нет данных для филиала '{selected_branch}' на дату {selected_date}")
                    funnel_data = pd.DataFrame({'Этап': stages, 'Значение': [0] * len(stages)})
            else:
                filtered_by_date = df[df[('Дата', '')] == selected_date_dt]

                if not filtered_by_date.empty:
                    values = []
                    for stage in stages:
                        total = filtered_by_date[(stage, metric)].sum()
                        values.append(float(total))

                    funnel_data = pd.DataFrame({
                        'Этап': stages,
                        'Значение': values
                    })
                else:
                    st.warning(f"Нет данных на дату {selected_date}")
                    funnel_data = pd.DataFrame({'Этап': stages, 'Значение': [0] * len(stages)})

        # Нормализация если выбрана
        if normalize_values and not funnel_data.empty:
            max_value = funnel_data['Значение'].max()
            if max_value > 0:
                funnel_data['Значение'] = (funnel_data['Значение'] / max_value) * 100

        # Создание воронки
        if not funnel_data.empty:
            colors = color_options[selected_color]

            if funnel_orientation == 'Горизонтальная':
                # ГОРИЗОНТАЛЬНАЯ ВОРОНКА
                fig = go.Figure()

                # Получаем начальное значение (первый этап)
                first_value = funnel_data['Значение'].iloc[0]

                # Создаем горизонтальные столбцы для каждого этапа
                for i, (stage, value) in enumerate(zip(funnel_data['Этап'], funnel_data['Значение'])):
                    # Текст для отображения - процент от НАЧАЛЬНОГО значения
                    if show_values:
                        if i == 0:
                            # Первый этап - только значение
                            display_text = f"{value:.1f}"
                        else:
                            # Для остальных этапов считаем процент от НАЧАЛЬНОГО значения
                            if first_value > 0:
                                percent = (value / first_value) * 100
                                if show_percentage:
                                    display_text = f"{value:.1f} ({percent:.1f}%)"
                                else:
                                    display_text = f"{value:.1f}"
                            else:
                                if show_percentage:
                                    display_text = f"{value:.1f} (0%)"
                                else:
                                    display_text = f"{value:.1f}"
                    else:
                        display_text = None

                    fig.add_trace(go.Bar(
                        y=[stage],
                        x=[value],
                        name=stage,
                        orientation='h',
                        marker=dict(
                            color=colors[i % len(colors)],
                            line=dict(width=1, color='white')
                        ),
                        text=[display_text] if display_text else None,
                        textposition='inside',
                        textfont=dict(size=14, color='white'),
                        hovertemplate=f"<b>{stage}</b><br>{metric}: {value:.1f}" +
                                      (
                                          f"<br>От начального: {(value / first_value * 100):.1f}%" if i > 0 and first_value > 0 else "") +
                                      "<extra></extra>"
                    ))

                fig.update_layout(
                    title=f"Воронка продаж - {period_label} - {selected_branch if selected_branch != 'Все филиалы' else 'Все филиалы'}",
                    height=550,  # Увеличили высоту
                    barmode='group',
                    showlegend=False,
                    template='plotly_white',
                    font=dict(
                        size=16,  # УВЕЛИЧИЛИ основной шрифт
                        family="Arial, sans-serif"
                    ),
                    title_font=dict(
                        size=22,  # УВЕЛИЧИЛИ заголовок
                        family="Arial, sans-serif",
                        color='#1f77b4'
                    ),
                    margin=dict(t=120, l=200, r=60, b=100),  # Увеличили отступы
                    xaxis_title=metric,
                    yaxis_title="Этап продаж",
                    yaxis=dict(
                        autorange="reversed",
                        title_font=dict(size=18),  # УВЕЛИЧИЛИ шрифт заголовка оси Y
                        tickfont=dict(size=16)  # УВЕЛИЧИЛИ шрифт меток оси Y
                    ),
                    xaxis=dict(
                        title_font=dict(size=18),  # УВЕЛИЧИЛИ шрифт заголовка оси X
                        tickfont=dict(size=16)  # УВЕЛИЧИЛИ шрифт меток оси X
                    ),
                    plot_bgcolor='rgba(240, 240, 240, 0.1)'
                )
            else:
                # ВЕРТИКАЛЬНАЯ ВОРОНКА
                fig = go.Figure(go.Funnel(
                    y=funnel_data['Этап'],
                    x=funnel_data['Значение'],
                    textposition="inside",
                    textinfo="value+percent initial" if show_values else "none",
                    marker=dict(
                        color=colors[:len(funnel_data)],
                        line=dict(width=1, color='white')
                    ),
                    opacity=0.8
                ))

                # Добавляем кастомные проценты если нужно
                if show_values and show_percentage:
                    values = funnel_data['Значение'].tolist()
                    text_labels = []
                    for i in range(len(values)):
                        if i == 0:
                            text_labels.append(f"{values[i]:.1f}")
                        else:
                            if values[i - 1] > 0:
                                percent = (values[i] / values[i - 1]) * 100.0
                                text_labels.append(f"{values[i]:.1f}<br>({percent:.1f}%)")
                            else:
                                text_labels.append(f"{values[i]:.1f}<br>(0%)")

                    fig.update_traces(
                        text=text_labels,
                        textposition="inside",
                        textfont=dict(size=12, color='white')
                    )

                fig.update_layout(
                    title=f"Воронка продаж - {period_label} - {selected_branch if selected_branch != 'Все филиалы' else 'Все филиалы'}",
                    height=600,  # Увеличили высоту
                    showlegend=False,
                    template='plotly_white',
                    font=dict(
                        size=14,  # Увеличили основной шрифт
                        family="Arial, sans-serif"
                    ),
                    title_font=dict(
                        size=20,  # Увеличили заголовок
                        family="Arial, sans-serif",
                        color='#1f77b4'
                    ),
                    margin=dict(t=100, l=80, r=50, b=80),  # Увеличили отступы
                    xaxis_title=metric,
                    yaxis_title="Этап продаж",
                )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных для построения воронки")

    with col2:
        st.subheader("📈 Конверсия между этапами")

        if 'funnel_data' in locals() and not funnel_data.empty:
            values = funnel_data['Значение'].tolist()

            if len(values) >= 2:
                conversion_rates = []
                for i in range(len(values) - 1):
                    if values[i] > 0:
                        rate = (values[i + 1] / values[i]) * 100
                        conversion_rates.append({
                            'Переход': f"{stages[i]} → {stages[i + 1]}",
                            'Конверсия': round(rate, 1)
                        })
                    else:
                        conversion_rates.append({
                            'Переход': f"{stages[i]} → {stages[i + 1]}",
                            'Конверсия': 0.0
                        })

                if conversion_rates:
                    conversion_df = pd.DataFrame(conversion_rates)

                    # Создаем стилизованную таблицу
                    st.dataframe(
                        conversion_df,
                        column_config={
                            "Конверсия": st.column_config.ProgressColumn(
                                "Конверсия, %",
                                format="%.1f%%",
                                min_value=0,
                                max_value=100,
                            )
                        },
                        hide_index=True,
                        use_container_width=True
                    )

                    # ИТОГОВАЯ конверсия (от первого к последнему этапу)
                    if values[0] > 0 and values[-1] > 0:
                        total_conversion = (values[-1] / values[0]) * 100
                        st.metric("Итоговая конверсия", f"{total_conversion:.1f}%")
                    elif values[0] > 0:
                        st.metric("Итоговая конверсия", "0%")
                    else:
                        st.metric("Итоговая конверсия", "0%")
                else:
                    st.info("Недостаточно данных для расчета конверсии")
            else:
                st.info("Недостаточно этапов для расчета конверсии")
        else:
            st.info("Загрузите данные для просмотра конверсии")

    # Детализированные данные
    st.markdown("---")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("📋 Детализированные данные")

        if selected_branch != 'Все филиалы':
            if period_option == 'За весь период':
                # Данные за весь период для конкретного филиала
                filtered_by_branch = df[df[('Филиал', '')] == selected_branch]
                display_data = []

                for stage in stages:
                    total_count = filtered_by_branch[(stage, 'Кол-во')].sum()
                    total_tonnage = filtered_by_branch[(stage, 'Тонн')].sum()

                    display_data.append({
                        'Этап': stage,
                        'Кол-во': float(total_count),
                        'Тонн': float(total_tonnage)
                    })

                display_df = pd.DataFrame(display_data)
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                if 'filtered_data' in locals() and not filtered_data.empty:
                    display_data = []

                    for stage in stages:
                        display_data.append({
                            'Этап': stage,
                            'Кол-во': float(filtered_data.iloc[0][(stage, 'Кол-во')]),
                            'Тонн': float(filtered_data.iloc[0][(stage, 'Тонн')])
                        })

                    display_df = pd.DataFrame(display_data)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Нет данных для выбранного филиала")
        else:
            # Для всех филиалов
            if period_option == 'За весь период':
                aggregated_data = []

                for stage in stages:
                    total_count = df[(stage, 'Кол-во')].sum()
                    total_tonnage = df[(stage, 'Тонн')].sum()

                    aggregated_data.append({
                        'Этап': stage,
                        'Кол-во': float(total_count),
                        'Тонн': float(total_tonnage)
                    })

                aggregated_df = pd.DataFrame(aggregated_data)
                st.dataframe(aggregated_df, use_container_width=True, hide_index=True)
            else:
                if 'filtered_by_date' in locals() and not filtered_by_date.empty:
                    aggregated_data = []

                    for stage in stages:
                        total_count = filtered_by_date[(stage, 'Кол-во')].sum()
                        total_tonnage = filtered_by_date[(stage, 'Тонн')].sum()

                        aggregated_data.append({
                            'Этап': stage,
                            'Кол-во': float(total_count),
                            'Тонн': float(total_tonnage)
                        })

                    aggregated_df = pd.DataFrame(aggregated_data)
                    st.dataframe(aggregated_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Нет данных для выбранной даты")

    with col2:
        st.subheader("📊 Статистика")

        if 'funnel_data' in locals() and not funnel_data.empty:
            values = funnel_data['Значение'].tolist()

            if values:
                col1_stats, col2_stats = st.columns(2)

                with col1_stats:
                    st.metric(
                        "Начальный этап",
                        f"{values[0]:.1f}",
                        help="Количество на первом этапе воронки"
                    )

                with col2_stats:
                    if values[-1] > 0:
                        st.metric(
                            "Конечный этап",
                            f"{values[-1]:.1f}",
                            help="Количество на последнем этапе воронки"
                        )

                # Общая конверсия
                if values[0] > 0 and values[-1] > 0:
                    total_conversion = (values[-1] / values[0]) * 100
                    st.metric("Общая конверсия", f"{total_conversion:.1f}%")

                # Потери
                losses = values[0] - values[-1]
                st.metric("Общие потери", f"{losses:.1f}")

                # Дополнительная статистика для всего периода
                if period_option == 'За весь период':
                    days_count = len(df[('Дата', '')].unique())
                    if days_count > 0:
                        avg_per_day = values[-1] / days_count
                        st.metric(
                            "Среднедневной результат",
                            f"{avg_per_day:.1f}"
                        )

    # Кнопка скачивания данных
    st.markdown("---")

    # Определяем, какой DataFrame использовать для скачивания
    download_df = None
    if selected_branch != 'Все филиалы' and 'display_df' in locals() and not display_df.empty:
        download_df = display_df
    elif selected_branch == 'Все филиалы' and 'aggregated_df' in locals() and not aggregated_df.empty:
        download_df = aggregated_df

    if download_df is not None:
        csv = download_df.to_csv(index=False).encode('utf-8')

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            st.download_button(
                label="📥 Скачать данные как CSV",
                data=csv,
                file_name=f"воронка_{selected_branch}_{'весь_период' if period_option == 'За весь период' else selected_date}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # Показ исходных данных если выбран
    if show_table:
        st.markdown("---")
        st.subheader("📄 Исходные данные")

        # Упрощаем отображение для лучшей читаемости
        display_columns = [('Дата', ''), ('Филиал', '')]
        for stage in stages[:3]:
            display_columns.append((stage, 'Кол-во'))
            display_columns.append((stage, 'Тонн'))

        preview_df = df[display_columns].head(20)

        # Преобразуем для лучшего отображения
        preview_display = preview_df.copy()
        preview_display[('Дата', '')] = preview_display[('Дата', '')].dt.strftime('%Y-%m-%d')

        # Округляем числа для читаемости
        for col in preview_display.columns:
            if col[1] in ['Кол-во', 'Тонн']:
                preview_display[col] = preview_display[col].apply(
                    lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else x
                )

        st.dataframe(preview_display, use_container_width=True)

        if len(df) > 20:
            st.caption(f"Показано 20 из {len(df)} записей. Загрузите полные данные для детального анализа.")

    # Инструкция
    with st.expander("ℹ️ Инструкция по использованию"):
        st.markdown("""
        ### Как пользоваться приложением:

        1. **Загрузите Excel-файл** через боковую панель
        2. **Выберите метрику** для анализа:
           - *Кол-во* - количество сделок/лидов
           - *Тонн* - объем в тоннах

        3. **Выберите период**:
           - *За весь период* - агрегированные данные за все даты
           - *Конкретная дата* - анализ за выбранный день

        4. **Выберите филиал** или "Все филиалы" для сводного анализа

        5. **Настройте отображение** графика:
           - Ориентация воронки (вертикальная/горизонтальная)
           - Цветовая схема
           - Отображение значений и процентов

        ### Интерпретация результатов:
        - **Воронка** показывает поток сделок через этапы
        - **Конверсия** между этапами показывает эффективность процесса
        - **Статистика** дает ключевые метрики эффективности

        ### Формат файла:
        Файл должен содержать столбцы:
        - Дата, Филиал
        - Для каждого этапа: Кол-во и Тонн
        - Этапы: Холодный, Встреча, КП, Согласование, Договор, Поставка
        """)

else:
    st.info("👈 Пожалуйста, загрузите Excel-файл через боковую панель для начала анализа")