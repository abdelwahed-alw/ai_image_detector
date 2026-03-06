use std::env;

fn calculate_covariance(image_path: &str) -> Option<(f32, f32, f32)> {
    let img = image::open(image_path).ok()?;
    let gray_img = img.to_luma8();
    let (width, height) = gray_img.dimensions();
    
    let mut m_matrix = Vec::new();
    for y in 1..(height - 1) {
        for x in 1..(width - 1) {
            let left = gray_img.get_pixel(x - 1, y)[0] as f32;
            let right = gray_img.get_pixel(x + 1, y)[0] as f32;
            let top = gray_img.get_pixel(x, y - 1)[0] as f32;
            let bottom = gray_img.get_pixel(x, y + 1)[0] as f32;
            m_matrix.push(((right - left) / 2.0, (bottom - top) / 2.0));
        }
    }

    let n = m_matrix.len() as f32;
    let (mut sxx, mut sxy, mut syy) = (0.0, 0.0, 0.0);
    for (gx, gy) in &m_matrix {
        sxx += gx * gx; sxy += gx * gy; syy += gy * gy;
    }
    Some((sxx / n, sxy / n, syy / n))
}

fn main() {
    // قراءة المسار من Argument (مثلاً: ./program image.png)
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 { return; }

    if let Some((c00, c01, c11)) = calculate_covariance(&args[1]) {
        // نطبع الأرقام بفاصلة فقط ليفهمها سكريبت بايثون بسهولة
        println!("{},{},{}", c00, c01, c11);
    }
}