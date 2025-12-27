import { ROLES, TESTIMONIAL } from "@/lib/data/home";

import { SectionHead } from "./SectionHead";

export function Roles() {
  return (
    <section className="section bg-ink">
      <div className="wrap">
        <SectionHead
          eyebrow="Built for the whole revenue team"
          title="One source of truth, four very different questions."
          titleStyle={{ color: "#fff" }}
        />
        <div className="roles">
          {ROLES.map((r) => (
            <div key={r.tag} className="role">
              <span className="tag">{r.tag}</span>
              <h3>&ldquo;{r.question}&rdquo;</h3>
              <p>{r.body}</p>
            </div>
          ))}
        </div>
        <div className="quote" style={{ marginTop: 80 }}>
          <blockquote>&ldquo;{TESTIMONIAL.quote}&rdquo;</blockquote>
          <cite>
            <b>{TESTIMONIAL.name}</b>, {TESTIMONIAL.role}
          </cite>
        </div>
      </div>
    </section>
  );
}
