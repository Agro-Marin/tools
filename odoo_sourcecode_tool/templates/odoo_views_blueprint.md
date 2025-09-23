# Odoo XML Views Blueprint

## XML View File Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Record definitions in specific order -->

    <!-- 1. Actions -->
    <!-- 2. Search Views -->
    <!-- 3. Tree/List Views -->
    <!-- 4. Form Views -->
    <!-- 5. Kanban Views -->
    <!-- 6. Graph Views -->
    <!-- 7. Pivot Views -->
    <!-- 8. Calendar Views -->
    <!-- 9. Gantt Views -->
    <!-- 10. Dashboard Views -->
    <!-- NOTE: Menu items must be in separate menu.xml file -->
</odoo>
```

## CRITICAL RULE: Menu Consolidation

**ALL menu items MUST be declared in a single `views/menu.xml` file**

This rule ensures:
- Centralized menu hierarchy management
- Easy menu reordering and organization
- Clear visibility of the module's navigation structure
- Prevention of scattered menu definitions
- Simplified menu debugging and maintenance

## View Components Order

### 1. Window Actions
```xml
<record id="action_model_name" model="ir.actions.act_window">
    <field name="name">Model Name</field>
    <field name="res_model">model.technical.name</field>
    <field name="view_mode">tree,form,kanban,graph,pivot,calendar</field>
    <field name="search_view_id" ref="view_model_name_search"/>
    <field name="domain">[]</field>
    <field name="context">{}</field>
    <field name="help" type="html">
        <p class="o_view_nocontent_smiling_face">
            Create your first record
        </p>
    </field>
</record>
```

### 2. Search View
```xml
<record id="view_model_name_search" model="ir.ui.view">
    <field name="name">model.name.search</field>
    <field name="model">model.technical.name</field>
    <field name="arch" type="xml">
        <search>
            <!-- Search Fields -->
            <field name="name" string="Name"/>
            <field name="partner_id"/>
            <field name="state"/>

            <!-- Filters -->
            <filter string="Active" name="active" domain="[('active','=',True)]"/>
            <filter string="Archived" name="inactive" domain="[('active','=',False)]"/>
            <separator/>
            <filter string="Draft" name="draft" domain="[('state','=','draft')]"/>
            <filter string="Confirmed" name="confirmed" domain="[('state','=','confirmed')]"/>
            <separator/>
            <filter string="My Records" name="my_records" domain="[('user_id','=',uid)]"/>

            <!-- Group By -->
            <group expand="0" string="Group By">
                <filter string="Partner" name="group_partner" context="{'group_by':'partner_id'}"/>
                <filter string="State" name="group_state" context="{'group_by':'state'}"/>
                <filter string="Company" name="group_company" context="{'group_by':'company_id'}"/>
                <filter string="Date" name="group_date" context="{'group_by':'date:month'}"/>
            </group>

            <!-- Search Panel (Odoo 13+) -->
            <searchpanel>
                <field name="state" enable_counters="1"/>
                <field name="partner_id" select="multi" enable_counters="1"/>
                <field name="company_id" groups="base.group_multi_company"/>
            </searchpanel>
        </search>
    </field>
</record>
```

### 3. Tree/List View
```xml
<record id="view_model_name_tree" model="ir.ui.view">
    <field name="name">model.name.tree</field>
    <field name="model">model.technical.name</field>
    <field name="arch" type="xml">
        <tree string="Model Name"
              decoration-info="state == 'draft'"
              decoration-success="state == 'done'"
              decoration-warning="state == 'pending'"
              decoration-danger="state == 'cancelled'"
              decoration-muted="active == False"
              default_order="sequence, id desc"
              multi_edit="1"
              sample="1">

            <!-- Optional Buttons -->
            <header>
                <button name="action_confirm" string="Confirm" type="object"/>
            </header>

            <!-- Fields -->
            <field name="sequence" widget="handle"/>
            <field name="name"/>
            <field name="partner_id"/>
            <field name="date"/>
            <field name="amount" sum="Total" avg="Average"/>
            <field name="state"
                   decoration-info="state == 'draft'"
                   decoration-success="state == 'done'"
                   widget="badge"/>
            <field name="company_id" groups="base.group_multi_company"/>
            <field name="active" invisible="1"/>

            <!-- Optional Inline Buttons -->
            <button name="action_done"
                    type="object"
                    string="Mark Done"
                    states="draft,pending"
                    icon="fa-check"/>
        </tree>
    </field>
</record>
```

### 4. Form View
```xml
<record id="view_model_name_form" model="ir.ui.view">
    <field name="name">model.name.form</field>
    <field name="model">model.technical.name</field>
    <field name="arch" type="xml">
        <form string="Model Name">
            <!-- Header with statusbar -->
            <header>
                <button name="action_confirm"
                        string="Confirm"
                        type="object"
                        class="btn-primary"
                        states="draft"/>
                <button name="action_cancel"
                        string="Cancel"
                        type="object"
                        states="draft,confirmed"/>
                <field name="state"
                       widget="statusbar"
                       statusbar_visible="draft,confirmed,done"/>
            </header>

            <!-- Main content -->
            <sheet>
                <!-- Title and buttons -->
                <div class="oe_button_box" name="button_box">
                    <button class="oe_stat_button"
                            type="object"
                            name="action_view_lines"
                            icon="fa-list">
                        <field string="Lines"
                               name="line_count"
                               widget="statinfo"/>
                    </button>
                </div>

                <!-- Widget/Title area -->
                <widget name="web_ribbon"
                        title="Archived"
                        bg_color="bg-danger"
                        attrs="{'invisible': [('active', '=', True)]}"/>

                <!-- Main fields -->
                <div class="oe_title">
                    <label for="name" class="oe_edit_only"/>
                    <h1>
                        <field name="name" placeholder="Name..."/>
                    </h1>
                </div>

                <!-- Groups for field organization -->
                <group>
                    <group name="left_group">
                        <field name="partner_id"
                               domain="[('is_company','=',True)]"
                               context="{'default_is_company': True}"/>
                        <field name="date"/>
                        <field name="user_id"/>
                    </group>
                    <group name="right_group">
                        <field name="amount" widget="monetary"/>
                        <field name="currency_id" invisible="1"/>
                        <field name="company_id"
                               groups="base.group_multi_company"/>
                        <field name="active" invisible="1"/>
                    </group>
                </group>

                <!-- Notebook for tabs -->
                <notebook>
                    <page string="Lines" name="lines">
                        <field name="line_ids"
                               context="{'default_parent_id': active_id}">
                            <tree editable="bottom">
                                <field name="sequence" widget="handle"/>
                                <field name="product_id"/>
                                <field name="quantity"/>
                                <field name="price_unit"/>
                                <field name="subtotal" sum="Total"/>
                            </tree>
                            <form>
                                <!-- Line form view -->
                            </form>
                        </field>
                        <group class="oe_subtotal_footer oe_right">
                            <field name="total_amount" widget="monetary"/>
                        </group>
                    </page>

                    <page string="Other Info" name="other_info">
                        <group>
                            <group>
                                <field name="notes"/>
                            </group>
                        </group>
                    </page>
                </notebook>
            </sheet>

            <!-- Chatter -->
            <div class="oe_chatter">
                <field name="message_follower_ids"/>
                <field name="activity_ids"/>
                <field name="message_ids"/>
            </div>
        </form>
    </field>
</record>
```

### 5. Kanban View
```xml
<record id="view_model_name_kanban" model="ir.ui.view">
    <field name="name">model.name.kanban</field>
    <field name="model">model.technical.name</field>
    <field name="arch" type="xml">
        <kanban default_group_by="state"
                class="o_kanban_mobile"
                sample="1">
            <!-- Fields to fetch -->
            <field name="name"/>
            <field name="partner_id"/>
            <field name="amount"/>
            <field name="state"/>
            <field name="color"/>
            <field name="priority"/>

            <!-- Progress bar -->
            <progressbar field="state"
                        colors='{"done": "success", "cancelled": "danger"}'/>

            <!-- Templates -->
            <templates>
                <t t-name="kanban-box">
                    <div class="oe_kanban_card oe_kanban_global_click">
                        <!-- Color indicator -->
                        <div class="o_kanban_record_top">
                            <div class="o_kanban_record_headings">
                                <strong class="o_kanban_record_title">
                                    <field name="name"/>
                                </strong>
                            </div>
                            <field name="priority" widget="priority"/>
                        </div>

                        <!-- Content -->
                        <div class="o_kanban_record_body">
                            <div>
                                <field name="partner_id"/>
                            </div>
                            <div>
                                <field name="amount" widget="monetary"/>
                            </div>
                        </div>

                        <!-- Bottom -->
                        <div class="o_kanban_record_bottom">
                            <div class="oe_kanban_bottom_left">
                                <field name="activity_ids" widget="kanban_activity"/>
                            </div>
                            <div class="oe_kanban_bottom_right">
                                <field name="user_id" widget="many2one_avatar_user"/>
                            </div>
                        </div>
                    </div>
                </t>
            </templates>
        </kanban>
    </field>
</record>
```

## View Inheritance Patterns

### Extension (Adding fields)
```xml
<record id="view_inherited_model_form" model="ir.ui.view">
    <field name="name">inherited.model.form</field>
    <field name="model">sale.order</field>
    <field name="inherit_id" ref="sale.view_order_form"/>
    <field name="arch" type="xml">
        <!-- Add after a field -->
        <field name="partner_id" position="after">
            <field name="custom_field"/>
        </field>

        <!-- Add inside a group -->
        <group name="left_group" position="inside">
            <field name="another_field"/>
        </group>

        <!-- Replace a field -->
        <field name="date_order" position="replace">
            <field name="date_order" readonly="1"/>
        </field>

        <!-- Add attributes -->
        <field name="partner_id" position="attributes">
            <attribute name="domain">[('customer_rank', '>', 0)]</attribute>
            <attribute name="invisible">state != 'draft'</attribute>
        </field>
    </field>
</record>
```

### Full Replacement
```xml
<record id="view_replace_form" model="ir.ui.view">
    <field name="name">model.form.replace</field>
    <field name="model">model.name</field>
    <field name="inherit_id" ref="module.view_original_form"/>
    <field name="mode">primary</field>
    <field name="arch" type="xml">
        <!-- Complete new form definition -->
    </field>
</record>
```

## Menu Structure (views/menu.xml)

### Menu File Organization
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- ============================================================ -->
    <!-- MAIN MENU ITEMS                                             -->
    <!-- ============================================================ -->

    <!-- Root menu entry -->
    <menuitem id="menu_main_module"
              name="Module Name"
              sequence="50"
              web_icon="module_name,static/description/icon.png"/>

    <!-- ============================================================ -->
    <!-- OPERATIONS MENU                                             -->
    <!-- ============================================================ -->

    <!-- First level - Operations -->
    <menuitem id="menu_module_operations"
              name="Operations"
              parent="menu_main_module"
              sequence="10"/>

    <!-- Second level - Individual models -->
    <menuitem id="menu_sale_orders"
              name="Sales Orders"
              parent="menu_module_operations"
              action="action_sale_order"
              sequence="10"/>

    <menuitem id="menu_sale_order_lines"
              name="Order Lines"
              parent="menu_module_operations"
              action="action_sale_order_line"
              sequence="20"/>

    <!-- ============================================================ -->
    <!-- REPORTING MENU                                              -->
    <!-- ============================================================ -->

    <menuitem id="menu_module_reporting"
              name="Reporting"
              parent="menu_main_module"
              sequence="50"/>

    <menuitem id="menu_sales_analysis"
              name="Sales Analysis"
              parent="menu_module_reporting"
              action="action_sales_analysis"
              sequence="10"/>

    <!-- ============================================================ -->
    <!-- CONFIGURATION MENU                                          -->
    <!-- ============================================================ -->

    <menuitem id="menu_module_configuration"
              name="Configuration"
              parent="menu_main_module"
              sequence="100"
              groups="base.group_system"/>

    <menuitem id="menu_settings"
              name="Settings"
              parent="menu_module_configuration"
              action="action_module_settings"
              sequence="10"/>
</odoo>
```

### Menu Hierarchy Best Practices

1. **Three-level maximum depth**
   - Main menu (module level)
   - Category menu (operations, reporting, configuration)
   - Action menu (specific views)

2. **Sequence ordering**
   - Operations: 10-40
   - Reporting: 50-80
   - Configuration: 90-100

3. **Naming conventions**
   - ID: `menu_[module]_[description]`
   - Name: User-friendly, translatable

4. **Security groups**
   - Apply at appropriate level
   - Configuration menus need admin groups

5. **Icons**
   - Only on root menu items
   - Use module's static/description/icon.png

## View Attributes Reference

### Common Attributes
- `string` - Display label
- `invisible` - Hide conditionally
- `readonly` - Make read-only conditionally
- `required` - Make required conditionally
- `domain` - Filter records
- `context` - Pass context
- `options` - Widget-specific options
- `widget` - Field widget
- `groups` - Security groups
- `attrs` - Dynamic attributes (deprecated, use individual attributes)

### Field Widgets
- **Char/Text**: `email`, `phone`, `url`, `html`, `copy_clipboard`
- **Numeric**: `monetary`, `percentage`, `progressbar`, `float_time`
- **Date**: `date`, `datetime`, `remaining_days`
- **Boolean**: `boolean_toggle`, `boolean_button`, `checkbox`
- **Selection**: `radio`, `badge`, `priority`, `state_selection`
- **Many2one**: `many2one_avatar`, `many2one_avatar_user`, `res_partner_many2one`
- **Many2many**: `many2many_tags`, `many2many_checkboxes`, `many2many_kanban`
- **One2many**: `one2many`, `one2many_list`
- **Binary**: `image`, `pdf_viewer`, `binary`
- **Special**: `handle` (for sequence), `color_picker`, `signature`

## Best Practices

1. **View Naming Convention**: `view_<model_name>_<view_type>`
2. **ID Naming**: Use underscores, prefix with module name for external use
3. **Inheritance**: Always use proper inherit_id references
4. **Groups**: Apply security groups appropriately
5. **Performance**: Avoid computed fields in tree views when possible
6. **Responsiveness**: Use proper Bootstrap classes
7. **Consistency**: Follow Odoo's standard UI patterns
8. **Documentation**: Comment complex domain or context values
9. **Modularity**: Split large view files by model
10. **Order**: Define views in dependency order

## Anti-patterns to Avoid

1. **Inline styles** - Use classes instead
2. **Hardcoded strings** - Use translations
3. **Missing security** - Always consider groups
4. **Complex domains in XML** - Move to Python
5. **Duplicate IDs** - Ensure unique IDs
6. **Missing inheritance** - Extend don't replace when possible
7. **Poor organization** - One file per model
8. **Missing help** - Add help for empty views
9. **Ignoring view types** - Provide all relevant view types
10. **Breaking UI conventions** - Follow Odoo standards