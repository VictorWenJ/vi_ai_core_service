type KeyValueTableProps = {
  title: string;
  value: unknown;
};

const renderValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value, null, 2);
};

export function KeyValueTable({ title, value }: KeyValueTableProps): JSX.Element {
  if (!value || typeof value !== "object") {
    return (
      <section className="panel">
        <h3>{title}</h3>
        <p className="muted">No data.</p>
      </section>
    );
  }

  const entries = Object.entries(value as Record<string, unknown>);
  if (entries.length === 0) {
    return (
      <section className="panel">
        <h3>{title}</h3>
        <p className="muted">No data.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h3>{title}</h3>
      <table className="kv-table">
        <tbody>
          {entries.map(([key, itemValue]) => (
            <tr key={key}>
              <th>{key}</th>
              <td>
                <pre>{renderValue(itemValue)}</pre>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
