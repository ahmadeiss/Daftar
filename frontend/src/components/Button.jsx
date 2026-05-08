export default function Button({
  children,
  type = "button",
  variant = "primary",
  className = "",
  ...props
}) {
  const variants = {
    primary: "bg-palm text-white hover:bg-teal-800",
    secondary: "bg-white text-ink border border-slate-200 hover:bg-slate-50",
    danger: "bg-red-50 text-red-700 border border-red-200 hover:bg-red-100",
    plain: "bg-transparent text-palm hover:bg-teal-50",
  };

  return (
    <button
      type={type}
      className={`tap-target inline-flex items-center justify-center gap-2 rounded-card px-4 py-2.5 font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
