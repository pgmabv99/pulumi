package main

import (
	"fmt"

	"github.com/pulumi/pulumi-aws/sdk/v6/go/aws/s3"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
		// Create an AWS resource (S3 Bucket)
		bucket, err := s3.NewBucket(ctx, "my-bucket", nil)
		if err != nil {
			return err
		}
		fmt.Println("Debug information")
		bucket2, err := s3.NewBucket(ctx, "my-bucket2", nil)
		if err != nil {
			return err
		}

		// Export the name of the bucket
		ctx.Export("bucketName", bucket.ID())
		ctx.Export("bucketName2", bucket2.ID())
		return nil
	})
}
