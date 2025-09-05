# Guia de Manutenção do Cabeçalho

## Visão Geral

O sistema possui um cabeçalho moderno e responsivo que exibe informações da empresa. Este guia explica como personalizar e manter o cabeçalho sem quebrar as funcionalidades existentes.

## Estrutura do Cabeçalho

### Arquivos Envolvidos

1. **Template Principal**: `financas/templates/financas/base.html`
2. **Estilos CSS**: `financas/static/financas/css/header.css`
3. **Context Processor**: `financas/context_processors.py`
4. **Configuração**: `financeiro/settings.py`

## Como Personalizar

### 1. Alterando Informações da Empresa

Edite o arquivo `financas/context_processors.py`:

```python
def company_info(request):
    return {
        'COMPANY_INFO': {
            'name': 'Sua Empresa',           # Nome da empresa
            'logo_icon': 'fas fa-building',  # Ícone do FontAwesome
            'phone': '(11) 1234-5678',       # Telefone
            'email': 'contato@suaempresa.com', # Email
            'website': 'www.suaempresa.com',   # Website
            'description': 'Descrição da empresa' # Tooltip
        }
    }
```

### 2. Personalizando Cores e Estilos

Edite o arquivo `financas/static/financas/css/header.css`:

```css
.main-header {
    background: linear-gradient(135deg, #sua-cor-1 0%, #sua-cor-2 100%);
    /* Outras propriedades... */
}
```

### 3. Alterando o Logo

Para usar uma imagem em vez de ícone:

1. Adicione a imagem em `financas/static/financas/images/`
2. Modifique o template `base.html`:

```html
<a href="..." class="logo">
    <img src="{% static 'financas/images/logo.png' %}" alt="Logo" style="height: 40px; margin-right: 10px;">
    <span>{{ COMPANY_INFO.name }}</span>
</a>
```

## Responsividade

O cabeçalho é totalmente responsivo:

- **Desktop**: Mostra logo + nome + informações completas
- **Tablet**: Oculta informações de contato
- **Mobile**: Mostra apenas o ícone

## Funcionalidades Implementadas

### ✅ Características

- **Fixo no topo**: Sempre visível durante a navegação
- **Responsivo**: Adapta-se a diferentes tamanhos de tela
- **Animações suaves**: Efeitos hover e transições
- **Tooltips informativos**: Ajuda contextual
- **Integração com sistema**: Não quebra rotas ou funcionalidades

### ✅ Compatibilidade

- **Usuários logados**: Cabeçalho + sidebar
- **Usuários não logados**: Apenas cabeçalho
- **Mobile**: Menu hambúrguer funcional
- **Todas as páginas**: Consistência visual

## Testando Mudanças

### 1. Verificação Básica
```bash
python manage.py check
```

### 2. Teste de Responsividade
- Redimensione a janela do navegador
- Teste em diferentes dispositivos
- Verifique se as informações aparecem/desaparecem corretamente

### 3. Teste de Funcionalidades
- Clique no logo (deve navegar corretamente)
- Verifique tooltips
- Teste navegação entre páginas
- Confirme que sidebar funciona normalmente

## Solução de Problemas

### Problema: Cabeçalho não aparece
**Solução**: Verifique se o CSS está sendo carregado:
```html
<link rel="stylesheet" href="{% static 'financas/css/header.css' %}">
```

### Problema: Informações não aparecem
**Solução**: Verifique se o context processor está configurado em `settings.py`:
```python
'financas.context_processors.company_info',
```

### Problema: Layout quebrado no mobile
**Solução**: Verifique as media queries no CSS e teste em diferentes resoluções.

## Melhores Práticas

1. **Sempre teste** após fazer mudanças
2. **Use o context processor** para dados dinâmicos
3. **Mantenha o CSS organizado** no arquivo separado
4. **Preserve a responsividade** ao fazer alterações
5. **Documente mudanças** significativas

## Backup e Versionamento

Antes de fazer mudanças importantes:

1. Faça backup dos arquivos originais
2. Teste em ambiente de desenvolvimento
3. Documente as alterações realizadas

---

**Nota**: Este cabeçalho foi projetado para ser facilmente mantido sem afetar as funcionalidades existentes do sistema financeiro.