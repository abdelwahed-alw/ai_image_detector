use std::env;

fn calculate_covariance(image_path: &str) -> Option<(f32, f32, f32)> {
    let img = image::open(image_path).ok()?;
    let gray_img = img.to_luma8();
    let (width, height) = gray_img.dimensions();
    
    let mut sxx = 0.0;
    let mut sxy = 0.0;
    let mut syy = 0.0;
    let mut n = 0.0;

    for y in 1..(height - 1) {
        for x in 1..(width - 1) {
            let left = gray_img.get_pixel(x - 1, y)[0] as f32;
            let right = gray_img.get_pixel(x + 1, y)[0] as f32;
            let top = gray_img.get_pixel(x, y - 1)[0] as f32;
            let bottom = gray_img.get_pixel(x, y + 1)[0] as f32;
            
            let gx = (right - left) / 2.0;
            let gy = (bottom - top) / 2.0;

            sxx += gx * gx;
            sxy += gx * gy;
            syy += gy * gy;
            n += 1.0;
        }
    }

    if n == 0.0 { return None; }

    Some((sxx / n, sxy / n, syy / n))
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 { return; }

    if let Some((c00, c01, c11)) = calculate_covariance(&args[1]) {
        println!("{},{},{}", c00, c01, c11);
    }
}