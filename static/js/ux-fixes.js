/**
 * UX Fixes - Fallback JavaScript
 * Remove rolagem horizontal dos widgets: E-mails, Relatórios, Visitas
 */

document.addEventListener('DOMContentLoaded', () => {
  // Seletores dos widgets problemáticos
  const sels = ['#visitas', '#relatorios', '#comunicacoes'];
  
  sels.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => {
      // Forçar overflow-x hidden
      el.style.overflowX = 'hidden';
      el.style.overflowY = 'auto';
      el.style.maxWidth = '100%';
      el.style.boxSizing = 'border-box';
      
      // Corrigir possíveis children com margin negativa que causam overflow
      el.querySelectorAll('*').forEach(ch => {
        const s = window.getComputedStyle(ch);
        if (parseFloat(s.marginLeft) < 0) ch.style.marginLeft = '0px';
        if (parseFloat(s.marginRight) < 0) ch.style.marginRight = '0px';
        
        // Garantir box-sizing em todos os elementos
        ch.style.boxSizing = 'border-box';
      });
    });
  });
  
  // Ajuste específico para tabelas dentro dos widgets
  const tableContainers = document.querySelectorAll('#visitas .table-responsive, #relatorios .table-responsive, #comunicacoes .table-responsive');
  tableContainers.forEach(container => {
    const table = container.querySelector('table');
    if (table) {
      table.style.tableLayout = 'fixed';
      table.style.width = '100%';
      table.style.wordBreak = 'break-word';
      
      // Ajustar células da tabela
      table.querySelectorAll('th, td').forEach(cell => {
        cell.style.whiteSpace = 'normal';
        cell.style.overflowWrap = 'anywhere';
        cell.style.wordBreak = 'break-word';
      });
    }
  });
  
  console.log('✅ UX Fixes aplicados: rolagem horizontal removida dos widgets');
});
