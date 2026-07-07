import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, ReferenceArea } from "recharts";

function PriceTrendChart({ data }) {
    if (!data || data.length === 0) return <p>データがありません</p>;

    const grouped = data.reduce((acc, item) => {
        const dateStr = item.date.slice(0, 10);
        if (!acc[dateStr]) acc[dateStr] = { prices: [], holiday: item.holiday };
        acc[dateStr].prices.push(Number(item.price_jpy));
        return acc;
    }, {});

    const chartData = Object.entries(grouped)
        .map(([date, { prices, holiday }]) => ({
            date,
            price_jpy: Math.round(prices.reduce((sum, p) => sum + p, 0) / prices.length),
            average_price: Number(data[0]?.average_price),
            holiday: holiday?.name || null
        }))
        .sort((a, b) => a.date.localeCompare(b.date));
    const obonStart = chartData.find(item => item.holiday === "お盆")?.date;
    const obonEnd = chartData.findLast(item => item.holiday === "お盆")?.date;
    const goldenWeekStart = chartData.find(item => item.holiday === "ゴールデンウィーク")?.date;
    const goldenWeekEnd = chartData.findLast(item => item.holiday === "ゴールデンウィーク")?.date;
    const newYearStart = chartData.find(item => item.holiday === "年末年始")?.date;
    return (
    <>
        <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 8, right: 16, left: 16, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }}
                    tickLine={false}
                />
                <YAxis
                    tickFormatter={(v) => `¥${(v/1000).toFixed(0)}k`}
                    tick={{ fontSize: 11, fontFamily: 'JetBrains Mono' }}
                    tickLine={false}
                    axisLine={false}
                />
                <Tooltip 
                    formatter={(value) => [value.toLocaleString('ja-JP', { style: 'currency', currency: 'JPY' }), '価格']}
                    labelStyle={{ fontFamily: 'JetBrains Mono', fontSize: 12 }}
                />
                <ReferenceLine 
                    y={chartData[0]?.average_price} 
                    stroke="#0D9488" 
                    strokeDasharray="4 4" 
                    label={{ value: '平均', fill: '#0D9488', fontSize: 11 }}
                />
                <Line 
                    type="monotone" 
                    dataKey="price_jpy" 
                    stroke="#111827" 
                    dot={false}
                    strokeWidth={1.5}
                />
                {obonStart &&<ReferenceArea 
                    x1={obonStart} 
                    x2={obonEnd} 
                    fill="#0D9488" 
                    fillOpacity={0.1}
                    label={{ value: "お盆", position: "insideTop", fontSize: 11, fill: "#0D9488" }}
                />}
                {goldenWeekStart &&<ReferenceArea 
                    x1={goldenWeekStart} 
                    x2={goldenWeekEnd} 
                    fill="#0D9488" 
                    fillOpacity={0.1}
                    label={{ value: "ゴールデンウィーク", position: "insideTop", fontSize: 11, fill: "#0D9488" }}
                />}
            </LineChart>
        </ResponsiveContainer>
        {newYearStart && (
            <p style={{ fontSize: 13, color: '#0D9488', marginTop: 8 }}>
                ⚠️ 年末年始（12/29〜1/3）は価格が高騰する傾向があります
            </p>
        )}
    </>
    );
}

export default PriceTrendChart;