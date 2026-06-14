import DemoBookingForm from "@/components/DemoBookingForm";

export default function DemoBook() {
  return (
    <main className="wrap">
      <section className="demo-hero">
        <h1>Book a job</h1>
        <p className="tagline">
          Pick a time that works. Mike confirms with one tap and you get a
          text back.
        </p>
      </section>
      <section style={{ paddingBottom: 40 }}>
        <DemoBookingForm />
      </section>
    </main>
  );
}
