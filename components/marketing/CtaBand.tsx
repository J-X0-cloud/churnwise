import { ButtonLink } from "@/components/ui/ButtonLink";
import { DEFAULT_CTA, TRIAL_URL } from "@/lib/data/site";

export function CtaBand({
  title = DEFAULT_CTA.title,
  body = DEFAULT_CTA.body,
}: {
  title?: string;
  body?: string;
}) {
  return (
    <section className="section-sm">
      <div className="wrap">
        <div className="cta-band">
          <div>
            <h2>{title}</h2>
            <p>{body}</p>
          </div>
          <div className="acts">
            <ButtonLink href={TRIAL_URL} variant="light" arrow>
              Start free trial
            </ButtonLink>
            <ButtonLink href="/demo" variant="ghost">
              Open live demo
            </ButtonLink>
          </div>
        </div>
      </div>
    </section>
  );
}
