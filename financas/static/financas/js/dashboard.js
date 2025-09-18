document.addEventListener('DOMContentLoaded', function() {
    // Inicializar seletor de mês
    initMonthSelector();
    
    // Inicializar filtros de transação
    initTransactionFilters();
    
    // Inicializar gráficos
    initCharts();
});

/**
 * Inicializa o seletor de mês com funcionalidade de dropdown
 */
function initMonthSelector() {
    const monthSelectorBtn = document.getElementById('monthSelectorBtn');
    const monthSelectorDropdown = document.getElementById('monthSelectorDropdown');
    const monthItems = document.querySelectorAll('.month-selector-item');
    
    if (!monthSelectorBtn || !monthSelectorDropdown) return;
    
    // Toggle dropdown ao clicar no botão
    monthSelectorBtn.addEventListener('click', function() {
        monthSelectorDropdown.classList.toggle('show');
    });
    
    // Fechar dropdown ao clicar fora
    document.addEventListener('click', function(event) {
        if (!monthSelectorBtn.contains(event.target) && !monthSelectorDropdown.contains(event.target)) {
            monthSelectorDropdown.classList.remove('show');
        }
    });
    
    // Selecionar mês ao clicar em um item
    monthItems.forEach(item => {
        item.addEventListener('click', function() {
            const month = this.getAttribute('data-month');
            const year = this.getAttribute('data-year');
            const monthText = this.textContent;
            
            // Atualizar texto do botão
            monthSelectorBtn.querySelector('span').textContent = monthText;
            
            // Remover classe active de todos os itens
            monthItems.forEach(i => i.classList.remove('active'));
            
            // Adicionar classe active ao item selecionado
            this.classList.add('active');
            
            // Fechar dropdown
            monthSelectorDropdown.classList.remove('show');
            
            // Redirecionar para a URL com o mês e ano selecionados
            window.location.href = `?month=${month}&year=${year}`;
        });
    });
}

/**
 * Inicializa os filtros de transação
 */
function initTransactionFilters() {
    const filterForm = document.getElementById('transactionFilters');
    const resetBtn = document.getElementById('resetFilters');
    
    if (!filterForm || !resetBtn) return;
    
    // Resetar filtros ao clicar no botão
    resetBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Limpar todos os campos do formulário
        const inputs = filterForm.querySelectorAll('input:not([type=submit]), select');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
        
        // Submeter o formulário para atualizar a página
        filterForm.submit();
    });
}

/**
 * Inicializa os gráficos do dashboard
 */
function initCharts() {
    // Verificar se o elemento do gráfico existe
    const chartElement = document.getElementById('graficoCategoria');
    if (!chartElement) {
        console.log('Elemento do gráfico não encontrado');
        return;
    }
    
    // Os gráficos são inicializados diretamente no template
    // Esta função apenas garante que o elemento do gráfico existe
    console.log('Inicialização de gráficos delegada ao template');
}

/**
 * Formata um valor para moeda brasileira
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}