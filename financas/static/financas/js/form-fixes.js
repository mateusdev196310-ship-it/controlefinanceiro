// Correções para problemas no formulário de transações
document.addEventListener('DOMContentLoaded', function() {
    // Corrigir problema de visibilidade no campo de valor
    const valorInput = document.getElementById('valor');
    if (valorInput) {
        // Remover qualquer formatação automática que possa estar causando problemas
        valorInput.addEventListener('input', function(e) {
            // Garantir que o valor permaneça visível
            this.style.color = 'inherit';
            this.style.opacity = '1';
        });
        
        // Corrigir problema de foco
        valorInput.addEventListener('focus', function(e) {
            this.style.color = 'inherit';
            this.style.opacity = '1';
        });
        
        // Prevenir comportamentos estranhos no blur
        valorInput.addEventListener('blur', function(e) {
            this.style.color = 'inherit';
            this.style.opacity = '1';
        });
    }
    
    // Corrigir problema de limpeza do formulário
    const form = document.querySelector('form[method="post"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            console.log('Form submit interceptado');
            
            // Verificar se todos os campos obrigatórios estão preenchidos
            const requiredFields = form.querySelectorAll('[required]');
            let allValid = true;
            
            requiredFields.forEach(function(field) {
                console.log(`Campo ${field.name}: ${field.value}`);
                if (!field.value.trim()) {
                    allValid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            console.log(`Validação: ${allValid ? 'passou' : 'falhou'}`);
            
            // Log da validação mas permitir submit
            if (!allValid) {
                console.log('Aviso: campos obrigatórios vazios, mas permitindo submit');
            }
            
            console.log('Formulário será submetido');
            
            // Desabilitar o botão de submit para evitar duplo clique
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
            }
        });
    }
    
    // Adicionar validação visual para campos obrigatórios
    const requiredInputs = document.querySelectorAll('input[required], select[required]');
    requiredInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (!this.value.trim()) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
        
        input.addEventListener('input', function() {
            if (this.value.trim()) {
                this.classList.remove('is-invalid');
            }
        });
    });
});