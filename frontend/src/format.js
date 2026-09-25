export function fmt(n) {
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export const LABEL = {
  revenue: "Revenue",
  cogs: "COGS",
  gross_profit: "Gross Profit",
  payroll: "Payroll",
  opex: "Operating Expenses",
  operating_profit: "Operating Profit",
};
