export function Faq({ title, items }: { title: string; items: Array<{ q: string; a: string }> }) {
  return (
    <div className="faq">
      <h2 style={{ textAlign: "center", marginBottom: 28 }}>{title}</h2>
      {items.map((item, i) => (
        <details key={item.q} open={i === 0}>
          <summary>{item.q}</summary>
          <p>{item.a}</p>
        </details>
      ))}
    </div>
  );
}
