export default function MainNavigation({ items, activePage, isSignedIn, onNavigate }) {
  return (
    <nav className="top-nav" aria-label="Main navigation">
      {items.map((item) => (
        <button key={item.id} className={`nav-item ${activePage === item.id ? 'active' : ''}`} onClick={() => onNavigate(item.id)}>
          <span>{item.label}</span>{item.protected && !isSignedIn && <span className="nav-lock">Login</span>}
        </button>
      ))}
    </nav>
  );
}
