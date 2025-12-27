import { FeatureIcon } from "@/components/ui/icons";
import type { IconName } from "@/components/ui/icons";

export function IconCards({ cards }: { cards: Array<{ icon: IconName; title: string; body: string }> }) {
  return (
    <div className="grid-3">
      {cards.map((card) => (
        <div key={card.title} className="card">
          <FeatureIcon name={card.icon} />
          <h3>{card.title}</h3>
          <p>{card.body}</p>
        </div>
      ))}
    </div>
  );
}
