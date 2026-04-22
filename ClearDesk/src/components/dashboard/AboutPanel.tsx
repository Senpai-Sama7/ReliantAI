export function AboutPanel() {
  return (
    <div className="max-w-6xl mx-auto">
      <iframe
        src="/about.html"
        title="About ClearDesk"
        className="w-full border-0 rounded-lg"
        style={{ height: 'calc(100vh - 120px)', minHeight: '600px' }}
      />
    </div>
  );
}
