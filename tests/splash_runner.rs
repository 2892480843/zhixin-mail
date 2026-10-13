use makepad_script::*;

fn main() {
    let path = std::env::args().nth(1).expect("script path");
    let code = std::fs::read_to_string(&path).expect("UTF-8 script");
    let mut host = ScriptVmHost::new(0i32, ());
    let mut vm = ScriptVm { host: &mut host, bx: Box::new(ScriptVmBase::new()) };
    let result = vm.eval(ScriptMod {
        module_path: "zhixin-regression".into(), file: path,
        code, ..Default::default()
    });
    vm.drain_errors();
    if result != ScriptValue::from(true) {
        eprintln!("regression failed: {result:?}");
        std::process::exit(1);
    }
}
