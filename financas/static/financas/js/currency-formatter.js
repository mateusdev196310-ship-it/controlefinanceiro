/**
 * Formatador de valores monetários em tempo real
 * Formata automaticamente campos de entrada de valores no padrão brasileiro
 */

class CurrencyFormatter {
    constructor() {
        this.initializeFormatters();
    }

    /**
     * Inicializa os formatadores para todos os campos de valor monetário
     */
    initializeFormatters() {
        // Seleciona todos os campos que devem ser formatados como moeda
        const currencyFields = document.querySelectorAll('input[data-currency="true"], input[name="valor"], input[name="valor_total"]');
        
        currencyFields.forEach(field => {
            this.setupCurrencyField(field);
        });
    }

    /**
     * Configura um campo específico para formatação de moeda
     * @param {HTMLInputElement} field - Campo de entrada
     */
    setupCurrencyField(field) {
        // Remove atributos que podem interferir na formatação
        field.removeAttribute('step');
        field.type = 'text';
        
        // Define valor inicial formatado se houver
        if (field.value && !isNaN(parseFloat(field.value))) {
            field.value = this.formatCurrency(parseFloat(field.value));
        } else if (!field.value) {
            field.value = '0,00';
        }

        // Adiciona eventos
        field.addEventListener('input', (e) => this.handleInput(e));
        field.addEventListener('focus', (e) => this.handleFocus(e));
        field.addEventListener('blur', (e) => this.handleBlur(e));
        field.addEventListener('keydown', (e) => this.handleKeydown(e));
    }

    /**
     * Manipula entrada de dados no campo
     * @param {Event} event - Evento de input
     */
    handleInput(event) {
        const field = event.target;
        let value = field.value;
        
        // Remove tudo que não é dígito
        value = value.replace(/\D/g, '');
        
        // Se não há dígitos, define como 0
        if (!value) {
            value = '0';
        }
        
        // Converte para número e formata
        const numericValue = parseInt(value) / 100;
        field.value = this.formatCurrency(numericValue);
        
        // Dispara evento customizado para outros scripts que possam estar ouvindo
        field.dispatchEvent(new CustomEvent('currencyChanged', {
            detail: { numericValue: numericValue }
        }));
    }

    /**
     * Manipula foco no campo
     * @param {Event} event - Evento de focus
     */
    handleFocus(event) {
        const field = event.target;
        // Seleciona todo o texto para facilitar edição
        setTimeout(() => field.select(), 0);
    }

    /**
     * Manipula perda de foco
     * @param {Event} event - Evento de blur
     */
    handleBlur(event) {
        const field = event.target;
        
        // Garante que o valor está formatado corretamente
        const numericValue = this.parseNumericValue(field.value);
        field.value = this.formatCurrency(numericValue);
    }

    /**
     * Manipula teclas especiais
     * @param {Event} event - Evento de keydown
     */
    handleKeydown(event) {
        const allowedKeys = [
            'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
            'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
            'Home', 'End'
        ];
        
        // Permite teclas de controle
        if (allowedKeys.includes(event.key)) {
            return;
        }
        
        // Permite Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
        if (event.ctrlKey && ['a', 'c', 'v', 'x'].includes(event.key.toLowerCase())) {
            return;
        }
        
        // Permite apenas dígitos
        if (!/^[0-9]$/.test(event.key)) {
            event.preventDefault();
        }
    }

    /**
     * Formata um valor numérico como moeda brasileira
     * @param {number} value - Valor numérico
     * @returns {string} - Valor formatado
     */
    formatCurrency(value) {
        if (isNaN(value)) {
            value = 0;
        }
        
        return value.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    /**
     * Extrai valor numérico de uma string formatada
     * @param {string} formattedValue - Valor formatado
     * @returns {number} - Valor numérico
     */
    parseNumericValue(formattedValue) {
        if (!formattedValue) return 0;
        
        // Remove pontos (separadores de milhares) e substitui vírgula por ponto
        const cleanValue = formattedValue
            .replace(/\./g, '')
            .replace(',', '.');
        
        const numericValue = parseFloat(cleanValue);
        return isNaN(numericValue) ? 0 : numericValue;
    }

    /**
     * Obtém o valor numérico de um campo formatado
     * @param {HTMLInputElement} field - Campo de entrada
     * @returns {number} - Valor numérico
     */
    getNumericValue(field) {
        return this.parseNumericValue(field.value);
    }

    /**
     * Define o valor de um campo formatado
     * @param {HTMLInputElement} field - Campo de entrada
     * @param {number} value - Valor numérico
     */
    setNumericValue(field, value) {
        field.value = this.formatCurrency(value);
        field.dispatchEvent(new CustomEvent('currencyChanged', {
            detail: { numericValue: value }
        }));
    }
}

// Inicializa o formatador quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.currencyFormatter = new CurrencyFormatter();
});

// Exporta para uso em outros scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CurrencyFormatter;
}