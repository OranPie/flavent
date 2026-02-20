# Flavent Grammar Supplement (EBNF, Phase 2)

Date: 2026-02-18

This is a compact, implementation-aligned grammar supplement for contributor and user reference. It matches the current parser behavior and is intentionally pragmatic (not a formal proof grammar).

## Lexical Notes

- Indentation defines blocks (`INDENT`/`DEDENT` tokens).
- Tabs are invalid in source.
- Line and block comments are supported (`// ...`, `/* ... */`).
- String and bytes literals support common ASCII escapes and `\xNN`.
- Unknown escapes in string/bytes literals are currently preserved as literal text for compatibility.

## Program Structure

```ebnf
program        ::= { NL | DEDENT | top_item } [ run_stmt EOF ]
run_stmt       ::= "run" "(" ")"

top_item       ::= type_decl | const_decl | let_decl | need_decl
                 | fn_decl | pattern_decl
                 | mixin_decl | use_stmt | use_mixin_stmt | resolve_mixin_stmt
                 | sector_decl | on_handler
```

## Declarations

```ebnf
type_decl      ::= "type" qualified_name [ "[" ident { "," ident } "]" ] "=" (record_type | sum_or_alias)
record_type    ::= "{" [ field_decl { "," field_decl } [ "," ] ] "}"
field_decl     ::= ident ":" type_ref
sum_or_alias   ::= variant_decl "|" variant_decl { "|" variant_decl } | type_ref
variant_decl   ::= ident [ "(" [ type_ref { "," type_ref } ] ")" ]

const_decl     ::= "const" ident "=" expr
let_decl       ::= "let" ident "=" expr
need_decl      ::= "need" [ "(" need_attr { "," need_attr } ")" ] ident "=" expr
need_attr      ::= ident "=" STR

fn_decl        ::= "fn" [ "@" ident ] ident [ "[" ident { "," ident } "]" ]
                   "(" [ param { "," param } ] ")" [ "->" type_ref ] "=" fn_body
fn_body        ::= expr | "do" ":" block
param          ::= [ "*" | "**" ] ident ":" type_ref
```

## Modules, Mixins, and Sectors

```ebnf
use_stmt           ::= "use" qualified_name
use_mixin_stmt     ::= "use" "mixin" qualified_name version
resolve_mixin_stmt ::= "resolve" "mixin" "-" "conflict" ":" NL INDENT { prefer_rule [ NL ] } DEDENT
prefer_rule        ::= "prefer" qualified_name version "over" qualified_name version
version            ::= ident  (* must look like v<digits> *)

mixin_decl      ::= "mixin" qualified_name version "into" ( ("sector" ident) | [ "type" ] qualified_name )
                    ":" NL INDENT { mixin_item [ NL ] } DEDENT
mixin_item      ::= pattern_decl | mixin_fn_add | mixin_around | mixin_hook | mixin_field_add
mixin_fn_add    ::= "fn" ident "(" [ param { "," param } ] ")" [ "->" type_ref ] "=" fn_body
mixin_around    ::= "around" "fn" ident "(" [ param { "," param } ] ")" [ "->" type_ref ] ":" block
mixin_hook      ::= "hook" hook_point "fn" ident "(" [ param { "," param } ] ")" [ "->" type_ref ]
                    [ "with" "(" [ hook_opt { "," hook_opt } ] ")" ] "=" fn_body
hook_point      ::= "head" | "tail" | "invoke"
hook_opt        ::= ident "=" (STR | BOOL | INT | ident)
mixin_field_add ::= ident ":" type_ref

sector_decl     ::= "sector" ident ":" NL INDENT { sector_item [ NL ] } DEDENT
sector_item     ::= let_decl | need_decl | fn_decl | on_handler
```

Current implementation note:
- `hook` items are supported for both sector-target and type-target mixins.
- Type-target hook/around targets resolve against mixin-injected methods (`fn name(self: Type, ...)`).
- Hook options include duplicate-id conflict policy (`conflict=error|prefer|drop`).

## Handlers, Blocks, and Statements

```ebnf
on_handler      ::= "on" event_pattern [ "as" ident ] [ "when" expr ] "->" ( expr | "do" ":" block )
event_pattern   ::= qualified_name [ "(" [ expr { "," expr } [ "," ] ] ")" ]

block           ::= NL INDENT { stmt [ NL ] } DEDENT

stmt            ::= "let" ident "=" expr
                 | lvalue assign_op expr
                 | "if" expr ":" block [ "else" ":" block ]
                 | "for" ident "in" expr ":" block
                 | "match" expr ":" NL INDENT { pattern "->" ( expr | "do" ":" block ) [ NL ] } DEDENT
                 | "emit" expr
                 | "return" expr
                 | "stop" "(" ")"
                 | "yield" "(" ")"
                 | expr

assign_op       ::= "=" | "+=" | "-=" | "*=" | "/="
lvalue          ::= ident { ("." ident) | ("[" expr "]") }
```

## Expressions and Precedence

```ebnf
expr            ::= pipe_expr
pipe_expr       ::= binary_expr { "|>" binary_expr }
binary_expr     ::= unary_expr { binop unary_expr }   (* precedence table below *)
unary_expr      ::= ( "-" | "not" ) unary_expr | postfix_expr
postfix_expr    ::= primary { call_suffix | member_suffix | index_suffix | try_suffix }
call_suffix     ::= "(" [ call_arg { "," call_arg } [ "," ] ] ")"
call_arg        ::= expr | "*" expr | "**" expr | ident "=" expr
member_suffix   ::= "." ident
index_suffix    ::= "[" expr "]"
try_suffix      ::= "?"

primary         ::= INT | FLOAT | STR | BYTES | BOOL | ident
                 | "{" [ record_item { "," record_item } [ "," ] ] "}"
                 | "(" ")" | "(" expr ")" | "(" expr "," [ expr { "," expr } ] [ "," ] ")"
                 | "match" expr ":" NL INDENT { pattern "->" ( expr | "do" ":" block ) [ NL ] } DEDENT
                 | "await" qualified_name
                 | "rpc" ident "." ident "(" [ expr { "," expr } [ "," ] ] ")"
                 | "call" ident "." ident "(" [ expr { "," expr } [ "," ] ] ")"
                 | "proceed" "(" [ expr { "," expr } [ "," ] ] ")"
record_item     ::= ident "=" expr
```

Binary precedence (high → low):
1. `*`, `/`
2. `+`, `-`
3. `==`, `!=`, `<`, `<=`, `>`, `>=`
4. `and`
5. `or`
6. `|>` (pipe chain around binary expressions)

## Patterns

```ebnf
pattern         ::= "_" | BOOL | qualified_name [ "(" [ pattern { "," pattern } ] ")" ] | ident
```

Current heuristic:
- Single-name uppercase patterns are interpreted as constructor patterns.
- Single-name lowercase patterns are interpreted as variable binders.
