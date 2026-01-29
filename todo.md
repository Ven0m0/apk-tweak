# TODO

integrate https://github.com/Graywizard888/Enhancify

```bash
    notify info "Removing unused libs..."
    find "$TEMP_DIR/lib" -mindepth 1 -maxdepth 1 -type d \
        ! -name "$ARCH" -exec rm -rf {} + &>/dev/null
    notify info "Removing old signature blocks..."
    if [[ -d "$TEMP_DIR/META-INF" ]]; then
        find "$TEMP_DIR/META-INF" \( -iname "*.SF" -o -iname "*.MF" -o -iname "*.RSA" -o -iname "*.DSA" -o -iname "*.EC" \) -delete
    fi
```

- https://github.com/Graywizard888/Enhancify/blob/main/modules/app/Optimize_Libs.sh
- https://github.com/Graywizard888/Enhancify/blob/main/modules/app/antisplit_apkm.sh
- https://github.com/Graywizard888/Enhancify/blob/main/modules/app/antisplit_xapk.sh
