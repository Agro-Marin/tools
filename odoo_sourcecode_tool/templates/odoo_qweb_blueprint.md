# Odoo QWeb Templates Blueprint

## QWeb Template File Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Template definitions in specific order -->

    <!-- 1. Asset Templates (JS templates) -->
    <!-- 2. Website Layout Templates -->
    <!-- 3. Website Page Templates -->
    <!-- 4. Email Templates -->
    <!-- 5. Report Templates -->
    <!-- 6. Portal Templates -->
    <!-- 7. Component/Snippet Templates -->
</odoo>
```

## Template Types and Organization

### 1. Backend JavaScript Templates (`static/src/xml/`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates id="template" xml:space="preserve">

    <!-- Widget Template -->
    <t t-name="module_name.WidgetName">
        <div class="o_module_widget">
            <div class="o_widget_header">
                <span t-esc="widget.title"/>
            </div>
            <div class="o_widget_content">
                <t t-foreach="widget.items" t-as="item">
                    <div class="o_item" t-att-data-id="item.id">
                        <span t-esc="item.name"/>
                        <span t-esc="item.value" t-att-class="item.value > 0 ? 'text-success' : 'text-danger'"/>
                    </div>
                </t>
            </div>
        </div>
    </t>

    <!-- Dialog Template -->
    <t t-name="module_name.DialogTemplate">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title">
                        <t t-esc="title"/>
                    </h4>
                    <button type="button" class="close" data-dismiss="modal">×</button>
                </div>
                <div class="modal-body">
                    <t t-raw="body"/>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary o_save">Save</button>
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                </div>
            </div>
        </div>
    </t>

</templates>
```

### 2. Website Templates (`views/templates.xml`)
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Website Layout Extension -->
    <template id="layout" inherit_id="website.layout" name="Module Layout">
        <xpath expr="//head" position="inside">
            <link rel="stylesheet" href="/module_name/static/src/css/website.css"/>
        </xpath>
    </template>

    <!-- Website Page Template -->
    <template id="page_template" name="Page Name">
        <t t-call="website.layout">
            <div id="wrap">
                <div class="container">
                    <!-- Breadcrumb -->
                    <nav aria-label="breadcrumb">
                        <ol class="breadcrumb">
                            <li class="breadcrumb-item"><a href="/">Home</a></li>
                            <li class="breadcrumb-item active">Page</li>
                        </ol>
                    </nav>

                    <!-- Page Content -->
                    <div class="row">
                        <div class="col-lg-8">
                            <h1 t-esc="page_title"/>
                            <div t-raw="page_content"/>
                        </div>
                        <div class="col-lg-4">
                            <t t-call="module_name.sidebar_template"/>
                        </div>
                    </div>
                </div>
            </div>
        </t>
    </template>

    <!-- Reusable Component Template -->
    <template id="sidebar_template" name="Sidebar">
        <div class="sidebar">
            <h3>Related Items</h3>
            <ul class="list-unstyled">
                <t t-foreach="items" t-as="item">
                    <li>
                        <a t-att-href="item.url" t-esc="item.name"/>
                    </li>
                </t>
            </ul>
        </div>
    </template>

</odoo>
```

### 3. Email Templates (`data/mail_template_data.xml`)
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <record id="email_template_name" model="mail.template">
        <field name="name">Email Template Name</field>
        <field name="model_id" ref="model_model_technical_name"/>
        <field name="email_from">{{ object.company_id.email or user.email }}</field>
        <field name="email_to">{{ object.partner_id.email }}</field>
        <field name="subject">{{ object.company_id.name }} - {{ object.name }}</field>
        <field name="body_html" type="html">
<![CDATA[
<div style="font-family: 'Lucida Grande', Ubuntu, Arial, sans-serif; font-size: 12px;">
    <p>Dear <t t-esc="object.partner_id.name"/>,</p>

    <p>Your order <strong t-esc="object.name"/> has been confirmed.</p>

    <table border="1" width="100%" cellpadding="0" cellspacing="0">
        <thead>
            <tr>
                <th>Product</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Subtotal</th>
            </tr>
        </thead>
        <tbody>
            <t t-foreach="object.line_ids" t-as="line">
                <tr>
                    <td><t t-esc="line.product_id.name"/></td>
                    <td><t t-esc="line.quantity"/></td>
                    <td><t t-esc="line.price_unit" t-options='{"widget": "monetary", "display_currency": object.currency_id}'/></td>
                    <td><t t-esc="line.subtotal" t-options='{"widget": "monetary", "display_currency": object.currency_id}'/></td>
                </tr>
            </t>
        </tbody>
        <tfoot>
            <tr>
                <td colspan="3">Total</td>
                <td><strong t-esc="object.amount_total" t-options='{"widget": "monetary", "display_currency": object.currency_id}'/></td>
            </tr>
        </tfoot>
    </table>

    <p>Best regards,<br/>
    <t t-esc="object.company_id.name"/></p>
</div>
]]>
        </field>
    </record>

</odoo>
```

### 4. Report Templates (`report/report_templates.xml`)
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Report Action -->
    <report id="report_model_name"
            model="model.technical.name"
            string="Report Name"
            report_type="qweb-pdf"
            name="module_name.report_template_name"
            file="module_name.report_template_name"
            print_report_name="'Report - %s' % (object.name)"/>

    <!-- Report Template -->
    <template id="report_template_name">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="o">
                <t t-call="web.external_layout">
                    <div class="page">
                        <!-- Header -->
                        <h2>
                            <span t-esc="o.name"/>
                        </h2>

                        <!-- Document Info -->
                        <div class="row mt32 mb32">
                            <div class="col-xs-6">
                                <strong>Date:</strong>
                                <span t-field="o.date"/>
                            </div>
                            <div class="col-xs-6">
                                <strong>Partner:</strong>
                                <span t-field="o.partner_id"/>
                            </div>
                        </div>

                        <!-- Table -->
                        <table class="table table-condensed">
                            <thead>
                                <tr>
                                    <th>Description</th>
                                    <th class="text-right">Quantity</th>
                                    <th class="text-right">Unit Price</th>
                                    <th class="text-right">Amount</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="o.line_ids" t-as="line">
                                    <tr>
                                        <td><span t-field="line.name"/></td>
                                        <td class="text-right">
                                            <span t-field="line.quantity"/>
                                            <span t-field="line.product_uom_id" groups="uom.group_uom"/>
                                        </td>
                                        <td class="text-right">
                                            <span t-field="line.price_unit"/>
                                        </td>
                                        <td class="text-right">
                                            <span t-field="line.price_subtotal"/>
                                        </td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>

                        <!-- Totals -->
                        <div class="row">
                            <div class="col-xs-4 pull-right">
                                <table class="table table-condensed">
                                    <tr>
                                        <td><strong>Total</strong></td>
                                        <td class="text-right">
                                            <span t-field="o.amount_total"
                                                  t-options='{"widget": "monetary", "display_currency": o.currency_id}'/>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </div>

                        <!-- Footer Notes -->
                        <div t-if="o.notes">
                            <strong>Notes:</strong>
                            <p t-field="o.notes"/>
                        </div>
                    </div>
                </t>
            </t>
        </t>
    </template>

</odoo>
```

### 5. Portal Templates (`views/portal_templates.xml`)
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Portal Layout -->
    <template id="portal_my_home_menu" name="Portal Menu" inherit_id="portal.portal_my_home">
        <xpath expr="//div[hasclass('o_portal_docs')]" position="inside">
            <t t-call="portal.portal_docs_entry">
                <t t-set="title">Custom Documents</t>
                <t t-set="url" t-value="'/my/custom'"/>
                <t t-set="count" t-value="custom_count"/>
            </t>
        </xpath>
    </template>

    <!-- Portal List View -->
    <template id="portal_my_custom" name="My Custom Documents">
        <t t-call="portal.portal_layout">
            <t t-set="breadcrumbs_searchbar" t-value="True"/>

            <t t-call="portal.portal_searchbar">
                <t t-set="title">Custom Documents</t>
            </t>

            <t t-if="documents" t-call="portal.portal_table">
                <thead>
                    <tr>
                        <th>Reference</th>
                        <th>Date</th>
                        <th>Status</th>
                        <th class="text-right">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <t t-foreach="documents" t-as="doc">
                        <tr>
                            <td>
                                <a t-att-href="'/my/custom/' + str(doc.id)">
                                    <t t-esc="doc.name"/>
                                </a>
                            </td>
                            <td><span t-field="doc.date"/></td>
                            <td>
                                <span t-field="doc.state" class="badge badge-pill badge-info"/>
                            </td>
                            <td class="text-right">
                                <span t-field="doc.amount_total"/>
                            </td>
                        </tr>
                    </t>
                </tbody>
            </t>
        </t>
    </template>

</odoo>
```

## QWeb Directives Reference

### Basic Directives
- `t-esc` - Escape and print value
- `t-raw` - Print raw HTML (unsafe)
- `t-field` - Print field with formatting
- `t-set` - Set a variable
- `t-value` - Set value attribute

### Conditionals
- `t-if` - Conditional rendering
- `t-elif` - Else if condition
- `t-else` - Else condition

### Loops
- `t-foreach` - Loop over items
- `t-as` - Loop variable name
- `*_index` - Current index (0-based)
- `*_size` - Total size
- `*_first` - Is first item
- `*_last` - Is last item
- `*_odd` - Is odd position
- `*_even` - Is even position

### Attributes
- `t-att-*` - Dynamic attribute
- `t-attf-*` - Formatted attribute
- `t-att` - Dictionary of attributes

### Calls
- `t-call` - Call another template
- `t-call-assets` - Include assets

### Utility
- `t-options` - Widget options for fields
- `t-translation` - Translation mode
- `t-cache` - Cache directive

## Template Organization Best Practices

### File Structure
```
views/
├── templates.xml          # Website templates
├── portal_templates.xml   # Portal templates
├── email_templates.xml    # Email templates
report/
├── report_templates.xml   # Report templates
static/src/xml/
├── dashboard_templates.xml # Backend JS templates
├── widget_templates.xml   # Widget templates
```

### Naming Conventions

#### Template IDs
- Website: `website_template_name`
- Portal: `portal_template_name`
- Report: `report_template_name`
- Email: `email_template_name`
- JS: `ModuleName.TemplateName`

#### CSS Classes
- Module specific: `o_module_name_*`
- Component: `o_component_*`
- Page specific: `o_page_*`

### Inheritance Patterns

#### Position Attributes
- `before` - Insert before
- `after` - Insert after
- `inside` - Append inside (default)
- `replace` - Replace element
- `attributes` - Modify attributes

#### XPath Expressions
```xml
<!-- By ID -->
<xpath expr="//div[@id='specific_id']" position="after">

<!-- By Class -->
<xpath expr="//div[hasclass('specific_class')]" position="inside">

<!-- By attribute -->
<xpath expr="//field[@name='partner_id']" position="after">

<!-- Complex -->
<xpath expr="//div[@class='container']//table[1]//tr[last()]" position="after">
```

## Performance Best Practices

1. **Minimize Loops** - Avoid nested t-foreach
2. **Use t-cache** - Cache expensive computations
3. **Lazy Loading** - Load content on demand
4. **Optimize Queries** - Prefetch related records
5. **Bundle Assets** - Combine CSS/JS files

## Security Best Practices

1. **Escape Output** - Use t-esc not t-raw
2. **Validate Input** - Check user permissions
3. **CSRF Protection** - Use proper tokens
4. **XSS Prevention** - Sanitize user content
5. **Access Control** - Check record rules

## Common Patterns

### Responsive Grid
```xml
<div class="container">
    <div class="row">
        <div class="col-12 col-md-6 col-lg-4" t-foreach="items" t-as="item">
            <!-- Item content -->
        </div>
    </div>
</div>
```

### Conditional Classes
```xml
<div t-attf-class="item-card #{item.active and 'active' or ''} #{item.featured and 'featured' or ''}">
```

### Money Formatting
```xml
<span t-field="doc.amount" t-options='{"widget": "monetary", "display_currency": doc.currency_id}'/>
```

### Date Formatting
```xml
<span t-field="doc.date" t-options='{"widget": "date"}'/>
<span t-field="doc.datetime" t-options='{"format": "dd/MM/yyyy HH:mm"}'/>
```

## Anti-patterns to Avoid

1. **Inline Styles** - Use CSS classes
2. **Complex Logic** - Move to Python
3. **Hardcoded Strings** - Use translations
4. **Missing Escaping** - Always escape user input
5. **Deep Nesting** - Flatten template structure
6. **Duplicate Templates** - Use inheritance
7. **Missing Error Handling** - Check for None/False
8. **Performance Issues** - Avoid N+1 queries
9. **Security Holes** - Never trust user input
10. **Poor Accessibility** - Include ARIA labels