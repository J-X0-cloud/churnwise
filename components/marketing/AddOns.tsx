import { ADD_ONS } from "@/lib/data/pricing";

export function AddOns() {
  return (
    <div className="addons">
      {ADD_ONS.map((a) => (
        <div key={a.name} className="addon">
          <div>
            <h3>{a.name}</h3>
            <p className="muted" style={{ margin: 0 }}>
              {a.summary}
            </p>
          </div>
          <div className="p">
            {a.price}
            <small>/mo</small>
          </div>
          <ul>
            {a.points.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
