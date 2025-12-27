/** The in-app banner and hosted card-update page, as a customer sees them. */
export function CardUpdatePreview() {
  return (
    <div className="paywall">
      <div className="bn">
        <span>Your last payment didn&apos;t go through. Update your card to keep your workspace active.</span>
        <a href="#">Update card</a>
      </div>
      <div className="pw-body">
        <h4 style={{ margin: "0 0 4px" }}>Update payment method</h4>
        <div className="field">
          <span>Card number</span>
          <b>•••• •••• •••• 1881</b>
        </div>
        <div className="grid-2" style={{ gap: 12 }}>
          <div className="field">
            <span>Expiry</span>
            <b>08 / 29</b>
          </div>
          <div className="field">
            <span>CVC</span>
            <b>•••</b>
          </div>
        </div>
        <a className="btn" href="#" style={{ width: "100%" }}>
          Save and retry payment
        </a>
        <p className="note" style={{ margin: 0, textAlign: "center" }}>
          Secure form hosted by Churnwise · your brand, your domain
        </p>
      </div>
    </div>
  );
}
