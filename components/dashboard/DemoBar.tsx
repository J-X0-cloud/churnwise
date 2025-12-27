import Link from "next/link";

import { TRIAL_URL } from "@/lib/data/site";

export function DemoBar() {
  return (
    <div className="demo-bar">
      <span>Live demo · sample data for a fictional SaaS company</span>
      <Link href="/">&larr; Back to churnwise.com</Link>
      <a href={TRIAL_URL}>Start your free trial</a>
    </div>
  );
}
