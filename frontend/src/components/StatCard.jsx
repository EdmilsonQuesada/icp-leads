import { Link } from "react-router-dom";

export function StatCard({ label, value, emoji, color, to }) {
  const colors = {
    red: "bg-red-50 border-red-200 text-red-700",
    yellow: "bg-yellow-50 border-yellow-200 text-yellow-700",
    blue: "bg-blue-50 border-blue-200 text-blue-700",
    gray: "bg-gray-50 border-gray-200 text-gray-700",
    green: "bg-green-50 border-green-200 text-green-700",
  };
  const inner = (
    <>
      <span className="text-2xl">{emoji}</span>
      <span className="text-3xl font-bold">{value}</span>
      <span className="text-sm font-medium">{label}</span>
    </>
  );
  const cls = `rounded-xl border p-4 flex flex-col gap-1 ${colors[color] || colors.gray}`;

  if (to) {
    return (
      <Link to={to} className={`${cls} hover:opacity-80 transition-opacity cursor-pointer`}>
        {inner}
      </Link>
    );
  }
  return <div className={cls}>{inner}</div>;
}
