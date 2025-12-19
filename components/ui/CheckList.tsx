import type { Check } from "@/lib/data/home";

export function CheckList({ items }: { items: Check[] }) {
  return (
    <ul className="checks">
      {items.map((item) => (
        <li key={item.lead}>
          <b>{item.lead}</b>
          {/^[,.;]/.test(item.rest) ? "" : " "}
          {item.rest}
        </li>
      ))}
    </ul>
  );
}
