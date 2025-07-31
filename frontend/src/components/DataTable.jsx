export function DataTable({ columns, rows, activeColumn, interactiveColumns = [], onHeaderClick }) {
  if (!rows?.length) {
    return <div className="empty-block">当前没有可展示的数据。</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => {
              const isInteractive = interactiveColumns.includes(column);
              const isActive = activeColumn === column;
              return (
                <th
                  key={column}
                  className={[
                    isInteractive ? "interactive-header" : "",
                    isActive ? "active-header" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={isInteractive ? () => onHeaderClick?.(column) : undefined}
                >
                  {column}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row[columns[0]] || "row"}-${index}`}>
              {columns.map((column) => (
                <td key={column}>{String(row[column] ?? "-")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
