import "./globals.css";

export const metadata = {
  title: "Goptant Blog",
  description: "A Medium-style blog starter built with Next.js and FastAPI.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
