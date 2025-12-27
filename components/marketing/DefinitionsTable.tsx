import { METRIC_DEFINITIONS } from "@/lib/data/product";

export function DefinitionsTable() {
  return (
    <div className="scroll-x">
      <table className="def-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>What it means</th>
            <th>Formula</th>
          </tr>
        </thead>
        <tbody>
          {METRIC_DEFINITIONS.map((d) => (
            <tr key={d.metric}>
              <td>{d.metric}</td>
              <td>{d.meaning}</td>
              <td>
                <code>{d.formula}</code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
